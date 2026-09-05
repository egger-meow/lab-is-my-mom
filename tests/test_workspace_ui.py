from pathlib import Path

from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event
from master_os.web.api import create_app
from research_os.core import Publication, Store


def make_client(tmp_path: Path):
    db = MasterDatabase(tmp_path / ".master-os" / "master.db")
    app = create_app(db, repo_root=tmp_path, agent_executors={})
    return TestClient(app), db


def test_workspace_navigation_is_served(tmp_path: Path):
    client, db = make_client(tmp_path)
    try:
        html = client.get("/").text
        assert "Tasks & Obligations" in html
        assert "Meetings" in html
        assert "Research" in html
        assert "Papers" in html
        assert "Agents" in html
        assert "使用說明" in html
        assert "/static/app.css" in html
        assert "/static/app.js" in html
    finally:
        db.close()


def test_onboarding_can_be_grounded_by_user_meeting_and_research_topic(tmp_path: Path):
    client, db = make_client(tmp_path)
    try:
        initial = client.get("/api/onboarding").json()
        assert initial["complete"] is False
        assert initial["research_topic"] is None

        meeting = client.post(
            "/api/meetings/schedule",
            json={
                "title": "Advisor Meeting",
                "kind": "advisor",
                "scheduled_at": "2026-09-10T14:00:00+08:00",
            },
        )
        assert meeting.status_code == 200
        meeting_id = meeting.json()["meeting_id"]
        stored = db.fetchone("SELECT * FROM meetings WHERE id=?", (meeting_id,))
        assert stored["scheduled_at"] == "2026-09-10T14:00:00+08:00"

        topic = "Uncertainty-Aware Selective Routing under Non-Stationary, Heterogeneous Costs"
        saved = client.post("/api/research/context", json={"topic": topic})
        assert saved.status_code == 200
        research = client.get("/api/research").json()
        assert research["topic"] == topic

        progress = client.get("/api/onboarding").json()
        by_id = {step["id"]: step for step in progress["steps"]}
        assert by_id["advisor_meeting"]["done"] is True
        assert by_id["research_topic"]["done"] is True
        assert by_id["meeting_transcript"]["done"] is False
    finally:
        db.close()


def test_workspace_task_status_and_lists_are_event_backed(tmp_path: Path):
    client, db = make_client(tmp_path)
    try:
        events = EventStore(db)
        source = events.register_source("user", "test", "workspace-test")
        event = events.record_event(
            "task.created",
            source.id,
            {
                "id": "T-workspace",
                "title": "Run baseline",
                "priority": "high",
                "agentability": "autonomous",
                "preferred_agent": "codex",
            },
            created_by="user_explicit",
        )
        apply_event(db, event)

        listing = client.get("/api/tasks").json()
        assert listing["tasks"][0]["id"] == "T-workspace"

        changed = client.post("/api/tasks/T-workspace/status", json={"status": "blocked"})
        assert changed.status_code == 200
        row = db.fetchone("SELECT status FROM tasks WHERE id='T-workspace'")
        assert row["status"] == "blocked"
        event_row = db.fetchone(
            "SELECT created_by FROM events WHERE event_type='task.status_changed' ORDER BY rowid DESC LIMIT 1"
        )
        assert event_row["created_by"] == "user_explicit"
    finally:
        db.close()


def test_papers_page_reads_existing_research_os_corpus(tmp_path: Path):
    store = Store(tmp_path)
    try:
        store.upsert_papers([
            Publication(
                title="A Useful Routing Paper",
                authors="An-Zi Yen and Student",
                year=2026,
                venue="ACL",
                category="conference",
                source_url="https://example.com/paper",
                evidence="source-backed publication entry",
            )
        ])
    finally:
        store.close()

    client, db = make_client(tmp_path)
    try:
        papers = client.get("/api/papers")
        assert papers.status_code == 200
        data = papers.json()
        assert data["available"] is True
        assert data["count"] == 1
        assert data["papers"][0]["title"] == "A Useful Routing Paper"
    finally:
        db.close()


def test_workspace_system_and_agents_endpoints_are_truthful_on_empty_db(tmp_path: Path):
    client, db = make_client(tmp_path)
    try:
        agents = client.get("/api/agents").json()
        assert agents["runs"] == []
        assert agents["interrupted"] == []

        system = client.get("/api/system")
        assert system.status_code == 200
        payload = system.json()
        assert "doctor" in payload
        assert "sources" in payload
        assert "schedules" in payload
        assert payload["master_database"].endswith("master.db")
    finally:
        db.close()
