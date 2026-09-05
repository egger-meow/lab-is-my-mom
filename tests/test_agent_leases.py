"""Regression tests for long-running agent lease safety."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from master_os.agents.packet import WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event
from master_os.supervisor.bootstrap import build_supervisor


def _create_task(db: MasterDatabase, task_id: str = "T-LEASE") -> None:
    events = EventStore(db)
    source = events.register_source("test", "Agent lease test", "agent-lease-test")
    event = events.record_event(
        "task.created",
        source.id,
        {
            "id": task_id,
            "title": "Run one exclusive agent job",
            "agentability": "autonomous",
            "preferred_agent": "codex",
            "acceptance_criteria": [],
        },
    )
    apply_event(db, event)


def _runtime(db: MasterDatabase, repo_root: Path) -> AgentRuntime:
    events = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root, events=events)
    return AgentRuntime(db, events, artifacts, repo_root)


def test_second_dispatch_for_same_task_is_rejected_while_first_run_is_active(tmp_path: Path):
    """Two processes/connections must not own the same task at the same time."""
    db_path = tmp_path / "master.db"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    db1 = MasterDatabase(db_path)
    _create_task(db1)
    db2 = MasterDatabase(db_path)

    entered = threading.Event()
    release = threading.Event()
    first_errors: list[BaseException] = []

    try:
        runtime1 = _runtime(db1, repo_root)
        runtime2 = _runtime(db2, repo_root)
        packet1 = WorkPacketBuilder(db1).build_packet(
            "T-LEASE",
            workspace_path=str(repo_root / ".master-os" / "worktrees" / "lease-a"),
            branch="agent/t-lease-a",
        )
        packet2 = WorkPacketBuilder(db2).build_packet(
            "T-LEASE",
            workspace_path=str(repo_root / ".master-os" / "worktrees" / "lease-b"),
            branch="agent/t-lease-b",
        )

        def slow_executor(_workspace: Path, _packet):
            entered.set()
            assert release.wait(timeout=5), "test did not release the first executor"
            return {"exit_code": 0, "artifacts": [], "findings": []}

        def run_first() -> None:
            try:
                runtime1.dispatch_autonomous_job(packet1, executor_func=slow_executor)
            except BaseException as exc:  # surfaced below after releasing the worker
                first_errors.append(exc)

        thread = threading.Thread(target=run_first, daemon=True)
        thread.start()
        assert entered.wait(timeout=5), "first agent run never entered its executor"

        with pytest.raises(RuntimeError, match="already.*active|active.*run|lease"):
            runtime2.dispatch_autonomous_job(
                packet2,
                executor_func=lambda _workspace, _packet: {
                    "exit_code": 0,
                    "artifacts": [],
                    "findings": [],
                },
            )

        release.set()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert first_errors == []
    finally:
        release.set()
        db2.close()
        db1.close()


def test_active_agent_run_renews_heartbeat_while_executor_is_running(tmp_path: Path):
    """A live long-running executor must keep proving liveness in SQLite."""
    db_path = tmp_path / "master.db"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    writer_db = MasterDatabase(db_path)
    _create_task(writer_db, "T-HEARTBEAT")
    observer_db = MasterDatabase(db_path)
    runtime = _runtime(writer_db, repo_root)
    # Production defaults can be conservative. The test accelerates the same loop.
    runtime.heartbeat_interval_seconds = 0.03

    packet = WorkPacketBuilder(writer_db).build_packet(
        "T-HEARTBEAT",
        workspace_path=str(repo_root / ".master-os" / "worktrees" / "heartbeat"),
        branch="agent/t-heartbeat",
    )
    entered = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []

    def slow_executor(_workspace: Path, _packet):
        entered.set()
        assert release.wait(timeout=5), "test did not release heartbeat executor"
        return {"exit_code": 0, "artifacts": [], "findings": []}

    def run_agent() -> None:
        try:
            runtime.dispatch_autonomous_job(packet, executor_func=slow_executor)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()

    try:
        assert entered.wait(timeout=5), "agent never entered executor"

        deadline = time.monotonic() + 1.0
        first_heartbeat = None
        while time.monotonic() < deadline:
            row = observer_db.fetchone(
                "SELECT heartbeat_at FROM agent_runs WHERE task_id = 'T-HEARTBEAT' AND status = 'running'"
            )
            if row and row["heartbeat_at"]:
                first_heartbeat = row["heartbeat_at"]
                break
            time.sleep(0.01)
        assert first_heartbeat is not None, "running agent never published an initial heartbeat"

        deadline = time.monotonic() + 1.0
        renewed = None
        while time.monotonic() < deadline:
            row = observer_db.fetchone(
                "SELECT heartbeat_at FROM agent_runs WHERE task_id = 'T-HEARTBEAT' AND status = 'running'"
            )
            if row and row["heartbeat_at"] and row["heartbeat_at"] != first_heartbeat:
                renewed = row["heartbeat_at"]
                break
            time.sleep(0.01)
        assert renewed is not None, "heartbeat timestamp never advanced while executor was still running"
    finally:
        release.set()
        thread.join(timeout=5)
        observer_db.close()
        writer_db.close()

    assert not thread.is_alive()
    assert errors == []


def test_supervisor_marks_stale_agent_run_interrupted_without_deleting_workspace(tmp_path: Path):
    """Restart recovery frees stale leases but preserves worktree evidence for inspection."""
    db = MasterDatabase(tmp_path / "master.db")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    workspace = repo_root / ".master-os" / "worktrees" / "stale-run"
    workspace.mkdir(parents=True)
    sentinel = workspace / "KEEP_ME.txt"
    sentinel.write_text("unfinished experiment evidence", encoding="utf-8")

    try:
        _create_task(db, "T-STALE")
        events = EventStore(db)
        source = events.register_source("agent_runner", "codex_runner", "runner-codex")
        started = events.record_event(
            "agent_run.started",
            source.id,
            {
                "id": "RUN-STALE",
                "agent_type": "codex",
                "job_type": "implementation",
                "task_id": "T-STALE",
                "workspace": str(workspace),
                "branch": "agent/t-stale",
                "base_git_sha": "deadbeef",
                "packet_artifact_id": None,
            },
            occurred_at="2026-09-05T00:00:00+00:00",
        )
        apply_event(db, started)
        db.execute(
            "UPDATE agent_runs SET heartbeat_at = ? WHERE id = ?",
            ("2026-09-05T00:00:30+00:00", "RUN-STALE"),
        )
        db.commit()

        supervisor = build_supervisor(
            db,
            repo_root,
            env={"MASTER_OS_AGENT_STALE_SECONDS": "60"},
        )
        now = datetime(2026, 9, 5, 1, 0, 0, tzinfo=timezone.utc)
        first = supervisor.run_once(now=now)

        run = db.fetchone("SELECT * FROM agent_runs WHERE id = 'RUN-STALE'")
        task = db.fetchone("SELECT * FROM tasks WHERE id = 'T-STALE'")
        assert run["status"] == "interrupted"
        assert run["finished_at"] is not None
        assert task["status"] == "blocked"
        assert sentinel.read_text(encoding="utf-8") == "unfinished experiment evidence"
        assert any(r.get("run_id") == "RUN-STALE" for r in first.get("recoveries", []))
        assert db.fetchone(
            "SELECT COUNT(*) AS n FROM events WHERE event_type = 'agent_run.interrupted'"
        )["n"] == 1

        # Recovery is replay-safe. Another supervisor tick must not invent another interruption.
        second = supervisor.run_once(now=now)
        assert second.get("recoveries", []) == []
        assert db.fetchone(
            "SELECT COUNT(*) AS n FROM events WHERE event_type = 'agent_run.interrupted'"
        )["n"] == 1
    finally:
        db.close()
