import pytest
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.commands import DomainCommandBus
from master_os.core.topics import TopicCommandService
from master_os.core.reducer import apply_event, rebuild_state
from master_os.core.assertions import AssertionResolver


def test_event_reduction_and_deterministic_rebuild(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    # 1. Execute flow
    topic = service.create_topic_seed("Topic R", "Question R", actor="user")
    hyp = service.add_hypothesis_version(topic.id, "Statement R", actor="user")
    service.activate_hypothesis_version(topic.id, hyp.id, expected_revision=1, actor="user")
    service.revise_policy(topic.id, hyp.id, min_viable_checks=["check_1"], actor="user")
    service.transition_status(topic.id, "exploring", expected_revision=2, actor="user")

    # Add and validate evidence, then transition to viable
    ev = service.link_evidence(
        topic.id,
        hyp.id,
        stance="supports",
        validation_status="under_review",
        limitations="None",
        actor="user",
    )
    service.review_evidence(ev.id, validation_status="validated", reason="Passed unit check", actor="user")
    service.transition_status(topic.id, "viable", expected_revision=3, actor="user")
    service.set_primary_topic(topic.id, actor="user")

    row_before = db.fetchone("SELECT * FROM topics WHERE id = ?", (topic.id,))
    assert row_before["status"] == "viable"
    assert row_before["revision"] == 4
    assert row_before["is_primary"] == 1

    ev_before = db.fetchone("SELECT * FROM evidence_links WHERE id = ?", (ev.id,))
    assert ev_before["validation_status"] == "validated"

    # 2. Clear materialized state
    db.clear_materialized_state()
    assert db.fetchone("SELECT id FROM topics WHERE id = ?", (topic.id,)) is None
    assert db.fetchone("SELECT id FROM evidence_links WHERE id = ?", (ev.id,)) is None

    # 3. Deterministically rebuild state from event log
    replayed = rebuild_state(db)
    assert replayed > 0

    row_after = db.fetchone("SELECT * FROM topics WHERE id = ?", (topic.id,))
    assert row_after is not None
    assert row_after["status"] == "viable"
    assert row_after["revision"] == 4
    assert row_after["is_primary"] == 1
    assert row_after["current_hypothesis_version_id"] == hyp.id

    ev_after = db.fetchone("SELECT * FROM evidence_links WHERE id = ?", (ev.id,))
    assert ev_after is not None
    assert ev_after["validation_status"] == "validated"


def test_topic_status_cannot_be_bypassed_via_assertions(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)
    resolver = AssertionResolver(db)

    topic = service.create_topic_seed("Topic No Bypass", "Question", actor="user")
    assert topic.status == "seed"

    # Try to assert status='selected' with high authority
    resolver.assert_field(
        subject_type="topic",
        subject_id=topic.id,
        field="status",
        value="selected",
        authority=500,  # USER_EXPLICIT
    )

    # Status must NOT be materialized onto topics table via assertion
    row = db.fetchone("SELECT status FROM topics WHERE id = ?", (topic.id,))
    assert row["status"] == "seed"
