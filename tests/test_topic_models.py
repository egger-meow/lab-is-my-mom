import pytest
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.models import (
    Topic,
    HypothesisVersion,
    ExplorationPolicy,
    EvidenceLink,
    AdvisorSignal,
    generate_id,
)


def test_topic_model_instantiation():
    topic = Topic(
        id=generate_id("TP-"),
        title="Contrastive Reranking for Low-Resource NLP",
        research_question="Does contrastive reranking improve zero-shot retrieval in low-resource settings?",
        status="seed",
        revision=1,
    )
    assert topic.status == "seed"
    assert topic.revision == 1
    assert topic.is_primary is False
    assert topic.blockers == []


def test_database_schema_initializes_topic_tables(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = MasterDatabase(db_path)

    # Verify tables exist
    tables = [r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "topics" in tables
    assert "hypothesis_versions" in tables
    assert "exploration_policies" in tables
    assert "evidence_links" in tables
    assert "advisor_signals" in tables
    assert "experiment_attempts" in tables


def test_clear_materialized_state_clears_topic_tables(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = MasterDatabase(db_path)

    topic_id = generate_id("TP-")
    db.execute(
        "INSERT INTO topics (id, title, research_question, status, revision, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (topic_id, "Test Topic", "Test Question", "seed", 1, "2026-09-14T00:00:00Z", "2026-09-14T00:00:00Z"),
    )
    db.commit()
    assert db.fetchone("SELECT id FROM topics WHERE id = ?", (topic_id,)) is not None

    db.clear_materialized_state()
    assert db.fetchone("SELECT id FROM topics WHERE id = ?", (topic_id,)) is None
