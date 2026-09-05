"""Regression tests for interrupted agent-run recovery UX and semantics."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event
from master_os.web.api import create_app


def _seed_interrupted_run(db: MasterDatabase, repo_root: Path) -> Path:
    events = EventStore(db)
    source = events.register_source("test", "Recovery test", "recovery-test")

    task = events.record_event(
        "task.created",
        source.id,
        {
            "id": "T-RECOVER",
            "title": "Repair interrupted research code",
            "status": "blocked",
            "agentability": "autonomous",
            "preferred_agent": "codex",
            "acceptance_criteria": [],
        },
    )
    apply_event(db, task)

    workspace = repo_root / ".master-os" / "worktrees" / "interrupted"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "KEEP_ME.txt").write_text("partial work", encoding="utf-8")

    started = events.record_event(
        "agent_run.started",
        source.id,
        {
            "id": "RUN-INTERRUPTED",
            "agent_type": "codex",
            "job_type": "implementation",
            "task_id": "T-RECOVER",
            "workspace": str(workspace),
            "branch": "agent/t-recover-old",
            "base_git_sha": None,
            "packet_artifact_id": None,
        },
    )
    apply_event(db, started)

    terminal = events.record_event(
        "agent_run.completed",
        source.id,
        {
            "id": "RUN-INTERRUPTED",
            "status": "interrupted",
            "exit_code": None,
            "result_git_sha": None,
            "result_artifact_id": None,
            "failure_id": None,
        },
    )
    apply_event(db, terminal)

    blocked = events.record_event(
        "task.status_changed",
        source.id,
        {"id": "T-RECOVER", "status": "blocked"},
    )
    apply_event(db, blocked)
    return workspace


def test_cockpit_and_inspect_surface_interrupted_run_without_mutating_it(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        workspace = _seed_interrupted_run(db, tmp_path)
        client = TestClient(create_app(db, repo_root=tmp_path))

        cockpit = client.get("/api/cockpit")
        assert cockpit.status_code == 200
        interrupted = cockpit.json()["what_needs_me"]["interrupted_runs"]
        assert [item["id"] for item in interrupted] == ["RUN-INTERRUPTED"]

        inspected = client.get("/api/agent-runs/RUN-INTERRUPTED/inspect")
        assert inspected.status_code == 200
        body = inspected.json()
        assert body["run"]["status"] == "interrupted"
        assert body["workspace_exists"] is True
        assert "KEEP_ME.txt" in body["workspace_files"]
        assert workspace.exists()
        assert db.fetchone("SELECT status FROM agent_runs WHERE id = 'RUN-INTERRUPTED'")["status"] == "interrupted"
    finally:
        db.close()


def test_resume_interrupted_run_reuses_workspace_and_supersedes_old_run(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        workspace = _seed_interrupted_run(db, tmp_path)

        def executor(actual_workspace: Path, _packet):
            assert actual_workspace == workspace.resolve()
            assert (actual_workspace / "KEEP_ME.txt").read_text(encoding="utf-8") == "partial work"
            (actual_workspace / "RESUMED.md").write_text("continued safely", encoding="utf-8")
            return {"exit_code": 0, "artifacts": ["RESUMED.md"], "findings": []}

        client = TestClient(create_app(db, repo_root=tmp_path, agent_executors={"codex": executor}))
        response = client.post(
            "/api/agent-runs/RUN-INTERRUPTED/recover",
            json={"action": "resume", "note": "continue partial work"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["action"] == "resume"
        assert body["new_run_id"] != "RUN-INTERRUPTED"
        assert db.fetchone("SELECT status FROM agent_runs WHERE id = 'RUN-INTERRUPTED'")["status"] == "superseded"
        assert db.fetchone("SELECT status FROM agent_runs WHERE id = ?", (body["new_run_id"],))["status"] == "completed"
        assert db.fetchone("SELECT status FROM tasks WHERE id = 'T-RECOVER'")["status"] == "completed"
        assert (workspace / "KEEP_ME.txt").exists()
        assert (workspace / "RESUMED.md").exists()
        relation = db.fetchone(
            "SELECT * FROM relations WHERE from_type='agent_run' AND from_id=? AND relation='recovered_from'",
            (body["new_run_id"],),
        )
        assert relation is not None
        assert relation["to_id"] == "RUN-INTERRUPTED"
    finally:
        db.close()


def test_retry_fresh_preserves_interrupted_workspace_and_uses_new_workspace(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        old_workspace = _seed_interrupted_run(db, tmp_path)
        observed: list[Path] = []

        def executor(actual_workspace: Path, _packet):
            observed.append(actual_workspace)
            assert actual_workspace != old_workspace.resolve()
            (actual_workspace / "RETRY.md").write_text("fresh retry", encoding="utf-8")
            return {"exit_code": 0, "artifacts": ["RETRY.md"], "findings": []}

        client = TestClient(create_app(db, repo_root=tmp_path, agent_executors={"codex": executor}))
        response = client.post(
            "/api/agent-runs/RUN-INTERRUPTED/recover",
            json={"action": "retry_fresh"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["action"] == "retry_fresh"
        assert len(observed) == 1
        assert old_workspace.exists()
        assert (old_workspace / "KEEP_ME.txt").exists()
        assert db.fetchone("SELECT status FROM agent_runs WHERE id = 'RUN-INTERRUPTED'")["status"] == "superseded"
        assert db.fetchone("SELECT status FROM tasks WHERE id = 'T-RECOVER'")["status"] == "completed"
    finally:
        db.close()


def test_abandon_interrupted_run_is_auditable_and_never_deletes_workspace(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        workspace = _seed_interrupted_run(db, tmp_path)
        client = TestClient(create_app(db, repo_root=tmp_path))

        response = client.post(
            "/api/agent-runs/RUN-INTERRUPTED/recover",
            json={"action": "abandon", "note": "obsolete approach"},
        )

        assert response.status_code == 200
        assert response.json()["action"] == "abandon"
        assert db.fetchone("SELECT status FROM agent_runs WHERE id = 'RUN-INTERRUPTED'")["status"] == "abandoned"
        assert db.fetchone("SELECT status FROM tasks WHERE id = 'T-RECOVER'")["status"] == "blocked"
        assert workspace.exists()
        assert (workspace / "KEEP_ME.txt").exists()
        assert db.fetchone("SELECT COUNT(*) AS n FROM agent_runs")["n"] == 1
        event = db.fetchone(
            "SELECT event_type, payload_json FROM events WHERE event_type = 'agent_run.recovery_decided' ORDER BY rowid DESC LIMIT 1"
        )
        assert event is not None
        assert '"action": "abandon"' in event["payload_json"]
    finally:
        db.close()
