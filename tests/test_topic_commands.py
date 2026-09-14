import pytest
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.commands import DomainCommandBus
from master_os.core.topics import (
    TopicCommandService,
    ConcurrencyConflictError,
    InvalidTransitionError,
    PermissionDeniedError,
)


def test_create_topic_seed(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    topic = service.create_topic_seed(
        title="Contrastive Reranker",
        research_question="Can contrastive loss improve small cross-encoders?",
        actor="user",
    )
    assert topic.status == "seed"
    assert topic.revision == 1
    assert topic.title == "Contrastive Reranker"


def test_transition_to_exploring_requires_hypothesis_and_policy(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    topic = service.create_topic_seed("Topic A", "Question A", actor="user")

    # Should fail because no hypothesis version and policy
    with pytest.raises(InvalidTransitionError, match="requires active hypothesis"):
        service.transition_status(topic.id, target_status="exploring", expected_revision=1, actor="user")

    hyp = service.add_hypothesis_version(topic.id, statement="Method X improves Y", actor="user")
    service.activate_hypothesis_version(topic.id, hyp.id, expected_revision=1, actor="user")

    with pytest.raises(InvalidTransitionError, match="requires exploration policy"):
        service.transition_status(topic.id, target_status="exploring", expected_revision=2, actor="user")

    service.revise_policy(topic.id, hyp.id, min_viable_checks=["check_baseline"], actor="user")

    # Now revision is updated to 2 after hypothesis activation
    updated = service.transition_status(topic.id, target_status="exploring", expected_revision=2, actor="user")
    assert updated.status == "exploring"
    assert updated.revision == 3


def test_transition_to_viable_requires_validated_supporting_evidence(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    topic = service.create_topic_seed("Topic Viable", "Question Viable", actor="user")
    hyp = service.add_hypothesis_version(topic.id, statement="Method V improves retrieval", actor="user")
    service.activate_hypothesis_version(topic.id, hyp.id, expected_revision=1, actor="user")
    service.revise_policy(topic.id, hyp.id, min_viable_checks=["check_dataset"], actor="user")
    service.transition_status(topic.id, target_status="exploring", expected_revision=2, actor="user")

    # Trying to jump to viable without validated supporting evidence fails
    with pytest.raises(InvalidTransitionError, match="validated supporting evidence"):
        service.transition_status(topic.id, target_status="viable", expected_revision=3, actor="user")

    # Link evidence as under_review
    ev = service.link_evidence(
        topic.id,
        hyp.id,
        stance="supports",
        validation_status="under_review",
        limitations="Small sample size",
        actor="user",
    )

    # Still under_review, should still fail
    with pytest.raises(InvalidTransitionError, match="validated supporting evidence"):
        service.transition_status(topic.id, target_status="viable", expected_revision=3, actor="user")

    # Review and validate evidence
    service.review_evidence(ev.id, validation_status="validated", reason="Reproduced locally", actor="user")

    # Now transition to viable succeeds
    updated = service.transition_status(topic.id, target_status="viable", expected_revision=3, actor="user")
    assert updated.status == "viable"
    assert updated.revision == 4


def test_agent_cannot_transition_to_selected_or_killed(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    topic = service.create_topic_seed("Topic B", "Question B", actor="user")

    # Agent tries to kill or select
    with pytest.raises(PermissionDeniedError, match="Only human user"):
        service.transition_status(topic.id, target_status="killed", expected_revision=1, actor="agent:codex", rationale="I decided to kill it")

    with pytest.raises(PermissionDeniedError, match="Only human user"):
        service.transition_status(topic.id, target_status="selected", expected_revision=1, actor="agent:antigravity", rationale="Looks good")


def test_optimistic_locking_conflict(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    topic = service.create_topic_seed("Topic C", "Question C", actor="user")

    # Passing wrong expected_revision
    with pytest.raises(ConcurrencyConflictError, match="Revision mismatch"):
        service.transition_status(topic.id, target_status="killed", expected_revision=999, actor="user", rationale="Drop it")


def test_primary_topic_assignment(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)

    topic1 = service.create_topic_seed("Topic 1", "Question 1", actor="user")
    topic2 = service.create_topic_seed("Topic 2", "Question 2", actor="user")

    service.set_primary_topic(topic1.id, actor="user")
    assert service.get_topic(topic1.id).is_primary is True
    assert service.get_topic(topic2.id).is_primary is False

    service.set_primary_topic(topic2.id, actor="user")
    assert service.get_topic(topic1.id).is_primary is False
    assert service.get_topic(topic2.id).is_primary is True
