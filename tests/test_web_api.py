"""Tests for Master OS Web Cockpit API and Endpoints."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.web.api import create_app


@pytest.fixture
def api_client(tmp_path: Path):
    db_path = tmp_path / "test_web.db"
    db = MasterDatabase(db_path)
    app = create_app(db, repo_root=tmp_path)
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

    # Verify the 5 core questions are directly answered in JSON
    assert "what_matters_now" in data
    assert "what_is_coming" in data
    assert "what_changed" in data
    assert "what_are_agents_doing" in data
    assert "what_needs_me" in data

    now = data["what_matters_now"]
    assert "focus_action" in now
    assert "research_velocity" in now


def test_end_to_end_web_flow(api_client):
    client, db = api_client

    # 1. Ingest meeting transcript via API
    ingest_payload = {
        "meeting_id": "M-20260910",
        "transcript_text": "Prof: VDAR baseline 下週看結果。 Student: 好，我會完成實作。",
    }
    res_ingest = client.post("/api/meetings/ingest", json=ingest_payload)
    assert res_ingest.status_code == 200
    assert "transcript_artifact_id" in res_ingest.json()

    # 2. Check Cockpit: what_matters_now should point to the new baseline task
    res_cockpit = client.get("/api/cockpit")
    data = res_cockpit.json()
    focus = data["what_matters_now"]["focus_action"]
    assert focus["task_id"] is not None
    assert "VDAR" in focus["title"]

    # 3. Autonomous dispatch of the focus task via API
    res_dispatch = client.post(f"/api/tasks/{focus['task_id']}/dispatch")
    assert res_dispatch.status_code == 200
    dispatch_data = res_dispatch.json()
    assert dispatch_data["status"] == "completed"
    assert len(dispatch_data["artifacts"]) > 0

    # 4. Generate Meeting Pack via API
    res_pack = client.post("/api/meetings/M-20260917/pack")
    assert res_pack.status_code == 200
    assert "Meeting Pack" in res_pack.json()["meeting_pack"]

    # 5. Create and decide approval
    from master_os.core.events import EventStore
    from master_os.core.artifacts import ArtifactRegistry
    from master_os.core.relations import RelationGraph
    from master_os.intelligence.meeting_agent import MeetingAgent

    agent = MeetingAgent(db, EventStore(db), ArtifactRegistry(db, Path(".")), RelationGraph(db), Path("."))
    ap_id = agent.create_post_meeting_slack_approval(
        meeting_id="M-20260910",
        meeting_title="個人 Meeting",
        date_str="2026-09-10",
        discussion_points=["確立 baseline"],
        next_commitments=["完成測試"],
    )

    res_decide = client.post(f"/api/approvals/{ap_id}/decide", json={"status": "approved", "note": "確認發送"})
    assert res_decide.status_code == 200
    assert res_decide.json()["status"] == "approved"
