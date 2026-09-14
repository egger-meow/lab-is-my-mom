import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.web.api import create_app


@pytest.fixture
def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = MasterDatabase(db_path)
    app = create_app(db, repo_root=tmp_path)
    return TestClient(app)


def test_api_topic_lifecycle(client: TestClient):
    # 1. Create seed
    resp = client.post(
        "/api/research/topics",
        json={
            "title": "API Topic",
            "research_question": "Can we test this via HTTP?",
            "actor": "user",
        },
    )
    assert resp.status_code == 200
    topic_data = resp.json()["topic"]
    topic_id = topic_data["id"]
    assert topic_data["status"] == "seed"
    assert topic_data["revision"] == 1

    # 2. Add and activate hypothesis
    resp = client.post(
        f"/api/research/topics/{topic_id}/hypotheses",
        json={
            "statement": "Hypothesis via API",
            "scope": "NLP",
            "actor": "user",
        },
    )
    assert resp.status_code == 200
    hyp_id = resp.json()["hypothesis"]["id"]

    resp = client.post(
        f"/api/research/topics/{topic_id}/hypotheses/{hyp_id}/activate",
        json={
            "expected_revision": 1,
            "actor": "user",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["topic"]["revision"] == 2

    # 3. Add policy
    resp = client.post(
        f"/api/research/topics/{topic_id}/policy",
        json={
            "hypothesis_version_id": hyp_id,
            "min_viable_checks": ["unit_test"],
            "actor": "user",
        },
    )
    assert resp.status_code == 200

    # 4. Transition to exploring
    resp = client.post(
        f"/api/research/topics/{topic_id}/transition",
        json={
            "target_status": "exploring",
            "expected_revision": 2,
            "actor": "user",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["topic"]["status"] == "exploring"

    # 5. Optimistic lock collision
    resp = client.post(
        f"/api/research/topics/{topic_id}/transition",
        json={
            "target_status": "viable",
            "expected_revision": 1,  # Stale!
            "actor": "user",
        },
    )
    assert resp.status_code == 409

    # 6. Link evidence and review
    resp = client.post(
        f"/api/research/topics/{topic_id}/evidence",
        json={
            "hypothesis_version_id": hyp_id,
            "stance": "supports",
            "validation_status": "under_review",
            "actor": "user",
        },
    )
    assert resp.status_code == 200
    ev_id = resp.json()["evidence"]["id"]

    resp = client.post(
        f"/api/research/topics/{topic_id}/evidence/{ev_id}/review",
        json={
            "validation_status": "validated",
            "reason": "Verified",
            "actor": "user",
        },
    )
    assert resp.status_code == 200

    # 7. Transition to viable
    resp = client.post(
        f"/api/research/topics/{topic_id}/transition",
        json={
            "target_status": "viable",
            "expected_revision": 3,
            "actor": "user",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["topic"]["status"] == "viable"

    # 8. Set primary
    resp = client.post(f"/api/research/topics/{topic_id}/primary", json={"actor": "user"})
    assert resp.status_code == 200

    # 9. GET topics list
    resp = client.get("/api/research/topics")
    assert resp.status_code == 200
    topics = resp.json()["topics"]
    assert len(topics) == 1
    assert topics[0]["is_primary"] is True
    assert topics[0]["evidence_counts"]["supports"] == 1


def test_api_agent_forbidden_from_selected(client: TestClient):
    resp = client.post(
        "/api/research/topics",
        json={
            "title": "Topic Agent Test",
            "research_question": "Will agent be blocked?",
            "actor": "user",
        },
    )
    topic_id = resp.json()["topic"]["id"]

    # Agent tries to select
    resp = client.post(
        f"/api/research/topics/{topic_id}/transition",
        json={
            "target_status": "selected",
            "expected_revision": 1,
            "actor": "agent:codex",
        },
    )
    assert resp.status_code == 403


def test_api_research_context_backward_compatibility(client: TestClient):
    # Old legacy context endpoint still works
    resp = client.post("/api/research/context", json={"topic": "Legacy Research Topic"})
    assert resp.status_code == 200

    resp = client.get("/api/research")
    assert resp.status_code == 200
    data = resp.json()
    assert data["topic"] == "Legacy Research Topic"
