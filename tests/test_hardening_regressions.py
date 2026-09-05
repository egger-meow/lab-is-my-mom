"""Regression tests for Master OS integrity boundaries."""
from pathlib import Path

from fastapi.testclient import TestClient

from master_os.agents.packet import WorkPacketBuilder
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.assertions import AssertionResolver
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import AuthorityLevel
from master_os.core.reducer import apply_event, rebuild_state
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.web.api import create_app


def _setup(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    events = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root=tmp_path)
    relations = RelationGraph(db)
    meeting_agent = MeetingAgent(db, events, artifacts, relations, repo_root=tmp_path)
    return db, events, artifacts, relations, meeting_agent


def test_neutral_transcript_does_not_fabricate_research_semantics(tmp_path: Path):
    db, _, _, _, agent = _setup(tmp_path)
    try:
        agent.ingest_transcript(
            "M-neutral",
            "Prof: 下週 meeting 改到星期五上午。 Student: 好，我知道了。",
        )

        assert db.fetchone("SELECT COUNT(*) AS n FROM decisions")["n"] == 0
        assert db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"] == 0
        assert db.fetchone("SELECT COUNT(*) AS n FROM tasks")["n"] == 0
    finally:
        db.close()


def test_work_packet_does_not_invent_repo_or_artifacts(tmp_path: Path):
    db, events, _, _, _ = _setup(tmp_path)
    try:
        source = events.register_source("system", "test", "hardening-test")
        event = events.record_event(
            "task.created",
            source.id,
            {
                "id": "T-hardening",
                "title": "Refactor parser",
                "acceptance_criteria": ["unit tests pass"],
            },
        )
        apply_event(db, event)

        packet = WorkPacketBuilder(db).build_packet(
            "T-hardening",
            workspace_path=str(tmp_path / "worktree"),
            repo_name="lab-is-my-mom",
        )

        assert packet.repo_name == "lab-is-my-mom"
        assert packet.expected_artifacts == []
    finally:
        db.close()


def test_web_dispatch_without_real_executor_cannot_fake_success(tmp_path: Path):
    db, events, _, _, _ = _setup(tmp_path)
    try:
        source = events.register_source("system", "test", "hardening-web")
        event = events.record_event(
            "task.created",
            source.id,
            {"id": "T-dispatch", "title": "Real coding task"},
        )
        apply_event(db, event)

        client = TestClient(create_app(db, repo_root=tmp_path))
        response = client.post("/api/tasks/T-dispatch/dispatch")

        assert response.status_code == 503
        assert db.fetchone("SELECT COUNT(*) AS n FROM findings")["n"] == 0
        assert db.fetchone("SELECT COUNT(*) AS n FROM artifacts")["n"] == 0
    finally:
        db.close()


def test_assertions_survive_deterministic_rebuild(tmp_path: Path):
    db, events, _, _, _ = _setup(tmp_path)
    try:
        source = events.register_source("system", "test", "hardening-assertion")
        event = events.record_event(
            "task.created",
            source.id,
            {"id": "T-assert", "title": "Important task", "priority": "medium"},
        )
        apply_event(db, event)

        resolver = AssertionResolver(db, events=events)
        resolver.assert_field(
            "task",
            "T-assert",
            "priority",
            "critical",
            authority=AuthorityLevel.USER_EXPLICIT,
        )
        assert db.fetchone("SELECT priority FROM tasks WHERE id = 'T-assert'")["priority"] == "critical"

        rebuild_state(db)

        assert db.fetchone("SELECT COUNT(*) AS n FROM assertions")["n"] == 1
        assert db.fetchone("SELECT priority FROM tasks WHERE id = 'T-assert'")["priority"] == "critical"
    finally:
        db.close()


def test_relations_survive_deterministic_rebuild(tmp_path: Path):
    db, events, _, _, _ = _setup(tmp_path)
    try:
        graph = RelationGraph(db, events=events)
        edge = graph.link("task", "T-a", "depends_on", "task", "T-b")
        assert edge.status == "active"

        rebuild_state(db)

        active = graph.get_out_relations("task", "T-a")
        assert len(active) == 1
        assert active[0].to_id == "T-b"
    finally:
        db.close()


def test_experiment_completion_does_not_self_validate_evidence(tmp_path: Path):
    db, events, _, _, _ = _setup(tmp_path)
    try:
        source = events.register_source("system", "test", "hardening-experiment")
        created = events.record_event(
            "experiment.created",
            source.id,
            {"id": "E-1", "title": "Baseline run"},
        )
        apply_event(db, created)

        finished = events.record_event(
            "experiment.finished",
            source.id,
            {"id": "E-1", "status": "completed"},
        )
        apply_event(db, finished)

        row = db.fetchone("SELECT validity_status FROM experiments WHERE id = 'E-1'")
        assert row["validity_status"] == "under_review"
    finally:
        db.close()
