"""Tests for Master OS Core Engine (Events, Assertions, Relations, Artifacts, Reducer)."""
from pathlib import Path
import pytest

from master_os.core.database import MasterDatabase
from master_os.core.models import AuthorityLevel, generate_id, Event
from master_os.core.events import EventStore
from master_os.core.assertions import AssertionResolver
from master_os.core.relations import RelationGraph
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.reducer import apply_event, rebuild_state


@pytest.fixture
def temp_db(tmp_path: Path):
    db_path = tmp_path / "test_master.db"
    db = MasterDatabase(db_path)
    yield db
    db.close()


def test_event_store_and_immutability(temp_db):
    store = EventStore(temp_db)
    source = store.register_source("manual_upload", "Meeting Notes", "meeting-2026-09-10.txt")
    assert source.id.startswith("S-")

    event = store.record_event(
        event_type="meeting.transcript.imported",
        source_id=source.id,
        payload={"title": "Advisor Meeting M-01", "scheduled_at": "2026-09-10T14:00:00Z"},
        raw_content="Professor said to implement VDAR baseline",
        dedup_key="transcript-m-01",
    )
    assert event.id.startswith("EV-")
    assert event.raw_hash is not None

    # Idempotent deduplication
    dup_event = store.record_event(
        event_type="meeting.transcript.imported",
        source_id=source.id,
        payload={"title": "Duplicate"},
        dedup_key="transcript-m-01",
    )
    assert dup_event.id == event.id


def test_assertion_resolver_authority_hierarchy(temp_db):
    resolver = AssertionResolver(temp_db)

    # First: Agent interpretation sets priority to medium
    resolver.assert_field(
        subject_type="task",
        subject_id="T-01",
        field="priority",
        value="medium",
        authority=AuthorityLevel.AGENT_INTERPRETATION,
        confidence=0.7,
    )

    resolved = resolver.resolve_field("task", "T-01", "priority")
    assert resolved is not None
    assert resolved.value == "medium"

    # Second: User explicit override sets priority to critical
    resolver.assert_field(
        subject_type="task",
        subject_id="T-01",
        field="priority",
        value="critical",
        authority=AuthorityLevel.USER_EXPLICIT,
        confidence=1.0,
    )

    resolved_override = resolver.resolve_field("task", "T-01", "priority")
    assert resolved_override is not None
    assert resolved_override.value == "critical"

    # Third: A lower authority (verified_source) tries to assert low, should NOT overwrite user explicit
    resolver.assert_field(
        subject_type="task",
        subject_id="T-01",
        field="priority",
        value="low",
        authority=AuthorityLevel.VERIFIED_SOURCE,
        confidence=0.9,
    )

    final_resolved = resolver.resolve_field("task", "T-01", "priority")
    assert final_resolved.value == "critical"


def test_relation_graph_and_invalidation(temp_db):
    graph = RelationGraph(temp_db)

    edge = graph.link("experiment", "E-01", "produced", "artifact", "A-01")
    assert edge.id.startswith("R-")
    assert edge.status == "active"

    out_edges = graph.get_out_relations("experiment", "E-01")
    assert len(out_edges) == 1
    assert out_edges[0].to_id == "A-01"

    # Invalidate edge
    graph.invalidate(edge.id)
    assert len(graph.get_out_relations("experiment", "E-01", status="active")) == 0
    assert len(graph.get_out_relations("experiment", "E-01", status="invalidated")) == 1


def test_artifact_registry_versioning(temp_db, tmp_path: Path):
    registry = ArtifactRegistry(temp_db, repo_root=tmp_path)
    file_path = tmp_path / "results.csv"
    file_path.write_text("accuracy,0.85\n")

    a1 = registry.register_file(file_path, artifact_type="experiment_metrics")
    assert a1.canonical is True
    assert registry.get_canonical("results.csv").id == a1.id

    # Modify file content -> new artifact version, previous marked non-canonical
    file_path.write_text("accuracy,0.89\n")
    a2 = registry.register_file(file_path, artifact_type="experiment_metrics")
    assert a2.id != a1.id
    assert a2.canonical is True

    old_a1 = registry.get_by_id(a1.id)
    assert old_a1.canonical is False


def test_deterministic_state_rebuild(temp_db):
    store = EventStore(temp_db)
    source = store.register_source("system", "Test Runner", "test-runner")

    # Emit several events
    e1 = store.record_event(
        "meeting.scheduled",
        source.id,
        {"id": "M-101", "title": "Individual Meeting", "scheduled_at": "2026-09-17T15:30:00Z"},
    )
    apply_event(temp_db, e1)

    e2 = store.record_event(
        "obligation.created",
        source.id,
        {"id": "O-101", "title": "Deliver VDAR baseline", "severity": "critical", "meeting_id": "M-101"},
    )
    apply_event(temp_db, e2)

    e3 = store.record_event(
        "task.created",
        source.id,
        {"id": "T-101", "title": "Implement routing baseline", "obligation_id": "O-101", "priority": "high"},
    )
    apply_event(temp_db, e3)

    # Verify materialized state exists
    m_row = temp_db.fetchone("SELECT * FROM meetings WHERE id = 'M-101'")
    assert m_row["title"] == "Individual Meeting"
    t_row = temp_db.fetchone("SELECT * FROM tasks WHERE id = 'T-101'")
    assert t_row["priority"] == "high"

    # Now rebuild state
    replayed_count = rebuild_state(temp_db)
    assert replayed_count == 3

    # State must be exactly identical
    m_rebuilt = temp_db.fetchone("SELECT * FROM meetings WHERE id = 'M-101'")
    assert m_rebuilt is not None
    assert m_rebuilt["title"] == "Individual Meeting"

    t_rebuilt = temp_db.fetchone("SELECT * FROM tasks WHERE id = 'T-101'")
    assert t_rebuilt is not None
    assert t_rebuilt["title"] == "Implement routing baseline"
