"""Regression coverage for obligation deadline health checks."""
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event


def test_critic_counts_actual_overdue_active_obligations(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("test", "test", "critic-deadlines")
        for oid, due_at in [
            ("O-OVERDUE", "2000-01-01T00:00:00+00:00"),
            ("O-FUTURE", "2999-01-01T00:00:00+00:00"),
        ]:
            event = events.record_event(
                "obligation.created",
                source.id,
                {"id": oid, "title": oid, "status": "pending", "due_at": due_at},
            )
            apply_event(db, event)

        report = MasterCritic(db).evaluate_health()
        assert report.active_obligations_count == 2
        assert report.overdue_obligations_count == 1
    finally:
        db.close()


def test_critic_ignores_closed_or_missing_deadlines(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("test", "test", "critic-closed-deadlines")
        closed = events.record_event(
            "obligation.created",
            source.id,
            {
                "id": "O-CLOSED",
                "title": "closed",
                "status": "satisfied",
                "due_at": "2000-01-01T00:00:00+00:00",
            },
        )
        no_due = events.record_event(
            "obligation.created",
            source.id,
            {"id": "O-NO-DUE", "title": "no due", "status": "pending"},
        )
        apply_event(db, closed)
        apply_event(db, no_due)

        report = MasterCritic(db).evaluate_health()
        assert report.active_obligations_count == 1
        assert report.overdue_obligations_count == 0
    finally:
        db.close()
