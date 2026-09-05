"""Tests for Master OS Web Cockpit API and endpoints."""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.web.api import create_app


@pytest.fixture
def api_client(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test_web.db")

    def test_codex_executor(path: Path, packet):
        reports = path / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "summary.md").write_text("# Test executor result\n", encoding="utf-8")
        return {"exit_code": 0, "artifacts": ["reports/summary.md"], "findings": []}

    app = create_app(db, repo_root=tmp_path, agent_executors={"codex": test_codex_executor})
    client = TestClient(app)
    yield client, db
    db.close()


def test_health_endpoint(api_client):
    client, _ = api_client
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"]["integrity_ok"] is True


def test_cockpit_five_questions_aggregation(api_client):
    client, _ = api_client
    res = client.get("/api/cockpit")
    assert res.status_code == 200
    data = res.json()
    assert "what_matters_now" in data
    assert "what_is_coming" in data
    assert "what_changed" in data
    assert "what_are_agents_doing" in data
    assert "what_needs_me" in data
    assert "focus_action" in data["what_matters_now"]
    assert "research_velocity" in data["what_matters_now"]


def test_end_to_end_web_flow_uses_confirmed_state_and_injected_executor(api_client):
    client, db = api_client

    # 1. Transcript creates semantic proposals, not automatic Tier-2 truth.
    ingest = client.post(
        "/api/meetings/ingest",
        json={
            "meeting_id": "M-20260910",
            "transcript_text": "Prof: 下次 meeting 請準備 baseline 結果。",
        },
    )
    assert ingest.status_code == 200
    approval_ids = ingest.json()["semantic_approval_ids"]
    assert approval_ids

    # 2. User explicitly confirms the obligation proposal.
    decided = client.post(
        f"/api/approvals/{approval_ids[0]}/decide",
        json={"status": "approved", "note": "確認是下次 meeting obligation"},
    )
    assert decided.status_code == 200
    assert decided.json()["materialized_entity_id"].startswith("O-")

    # 3. Create an executable task from confirmed workflow state.
    from master_os.core.events import EventStore
    from master_os.core.reducer import apply_event

    store = EventStore(db)
    source = store.register_source("user", "test", "web-e2e")
    task_event = store.record_event(
        "task.created",
        source.id,
        {
            "id": "T-web-e2e",
            "title": "Prepare baseline implementation",
            "priority": "critical",
            "agentability": "autonomous",
            "preferred_agent": "codex",
            "acceptance_criteria": ["test executor produced reports/summary.md"],
        },
        created_by="user_explicit",
    )
    apply_event(db, task_event)

    cockpit = client.get("/api/cockpit").json()
    assert cockpit["what_matters_now"]["focus_action"]["task_id"] == "T-web-e2e"

    # 4. Web request only durably queues/submits work. It must not wait for Codex.
    dispatch = client.post("/api/tasks/T-web-e2e/dispatch")
    assert dispatch.status_code == 202
    dispatch_data = dispatch.json()
    assert dispatch_data["status"] == "queued"
    assert dispatch_data["run_id"].startswith("RUN-")

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        row = db.fetchone("SELECT status FROM agent_runs WHERE id = ?", (dispatch_data["run_id"],))
        if row and row["status"] == "completed":
            break
        time.sleep(0.01)
    row = db.fetchone("SELECT status, result_artifact_id FROM agent_runs WHERE id = ?", (dispatch_data["run_id"],))
    assert row["status"] == "completed"
    assert row["result_artifact_id"] is not None

    # 5. Meeting pack is generated from stored state only.
    pack = client.post("/api/meetings/M-20260917/pack")
    assert pack.status_code == 200
    assert "Meeting Pack" in pack.json()["meeting_pack"]
    assert "86.4" not in pack.json()["meeting_pack"]
