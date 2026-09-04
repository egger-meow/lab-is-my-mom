"""Tests for Master OS Agent Runtime, Packet Builder, and Critic."""
from pathlib import Path
import pytest

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.reducer import apply_event
from master_os.agents.packet import WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.agents.critic import MasterCritic


@pytest.fixture
def test_setup(tmp_path: Path):
    db_path = tmp_path / "test_agents.db"
    db = MasterDatabase(db_path)
    store = EventStore(db)
    registry = ArtifactRegistry(db, repo_root=tmp_path)
    runtime = AgentRuntime(db, store, registry, repo_root=tmp_path)
    critic = MasterCritic(db)
    yield db, store, registry, runtime, critic
    db.close()


def test_packet_builder_injects_failure_memory(test_setup, tmp_path: Path):
    db, store, _, _, _ = test_setup
    source = store.register_source("system", "Test", "test")

    # Record a known failure
    fail_event = store.record_event(
        "failure.recorded",
        source.id,
        {
            "id": "F-27",
            "title": "Entropy Threshold Routing Collapse",
            "description": "Poor calibration across model families",
            "failure_type": "calibration_error",
            "root_cause": "Softmax confidence uncalibrated under cost drift",
            "resolution": "Use temperature scaling or selective margin",
            "retry_condition": "Do not retry without calibration correction",
            "status": "active",
        },
    )
    apply_event(db, fail_event)

    # Create obligation and task
    ob_event = store.record_event(
        "obligation.created",
        source.id,
        {"id": "O-01", "title": "Implement routing baseline for meeting", "severity": "critical"},
    )
    apply_event(db, ob_event)

    task_event = store.record_event(
        "task.created",
        source.id,
        {
            "id": "T-193",
            "title": "Implement VDAR baseline",
            "obligation_id": "O-01",
            "acceptance_criteria": ["pytest tests/test_vdar.py", "results/metrics.csv generated"],
        },
    )
    apply_event(db, task_event)

    builder = WorkPacketBuilder(db)
    packet = builder.build_packet("T-193", workspace_path=str(tmp_path / "worktree-193"))

    assert packet.task_id == "T-193"
    assert "Implement VDAR baseline" in packet.objective
    assert "O-01" in packet.why
    assert len(packet.known_failures) == 1
    assert packet.known_failures[0]["id"] == "F-27"
    assert "calibrat" in packet.known_failures[0]["root_cause"].lower()


def test_agent_runtime_acceptance_verification(test_setup, tmp_path: Path):
    db, store, registry, runtime, _ = test_setup
    source = store.register_source("system", "Test", "test")

    task_event = store.record_event(
        "task.created",
        source.id,
        {"id": "T-200", "title": "Run baseline benchmark", "acceptance_criteria": []},
    )
    apply_event(db, task_event)

    builder = WorkPacketBuilder(db)
    ws_path = tmp_path / "worktree-200"
    packet = builder.build_packet("T-200", workspace_path=str(ws_path))

    # Test executor that produces expected artifacts
    def mock_executor(path: Path, pkt):
        results_dir = path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        (results_dir / "metrics.csv").write_text("method,acc,cost\nVDAR,0.86,0.015\n")

        reports_dir = path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "summary.md").write_text("# Summary\nBaseline succeeded.")

        return {
            "exit_code": 0,
            "artifacts": ["results/metrics.csv", "reports/summary.md"],
            "findings": [{"statement": "VDAR achieves 86% accuracy with 15% cost reduction"}],
        }

    res = runtime.dispatch_autonomous_job(packet, executor_func=mock_executor)
    assert res["status"] == "completed"
    assert res["task_status"] == "completed"
    assert len(res["artifacts"]) == 2

    # Verify task in DB updated to completed
    task_row = db.fetchone("SELECT * FROM tasks WHERE id = 'T-200'")
    assert task_row["status"] == "completed"

    # Verify findings recorded
    findings = db.fetchall("SELECT * FROM findings")
    assert len(findings) == 1
    assert "VDAR achieves 86%" in findings[0]["statement"]


def test_master_critic_detects_fake_progress(test_setup):
    db, store, _, _, critic = test_setup
    source = store.register_source("system", "Test", "test")

    # Complete 4 tasks, but 0 experiments and 0 findings
    for i in range(4):
        e = store.record_event(
            "task.created",
            source.id,
            {"id": f"T-fake-{i}", "title": f"Format code {i}", "status": "completed"},
        )
        apply_event(db, e)
        e_comp = store.record_event(
            "task.status_changed",
            source.id,
            {"id": f"T-fake-{i}", "status": "completed"},
        )
        apply_event(db, e_comp)

    report = critic.evaluate_health()
    assert report.fake_progress_warning is True
    assert "Activity high, research progress low" in report.warning_message
