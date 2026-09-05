"""Second-wave regressions for long-lived Master OS runtime integrity."""
import re
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id
from master_os.core.reducer import rebuild_state
from master_os.scheduler.engine import SchedulerEngine


def test_database_supports_real_rollback(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        db.execute("CREATE TABLE rollback_probe (value TEXT)")
        db.commit()
        db.execute("INSERT INTO rollback_probe(value) VALUES ('not-committed')")
        db.rollback()
        assert db.fetchone("SELECT COUNT(*) AS n FROM rollback_probe")["n"] == 0
    finally:
        db.close()


def test_semantic_ids_use_collision_resistant_suffix():
    identifier = generate_id("EV-")
    assert re.fullmatch(r"EV-\d{8}-[0-9a-f]{12}", identifier)


def test_event_cursor_does_not_skip_same_timestamp_events(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("test", "test", "event-cursor")
        timestamp = "2026-09-05T00:00:00+00:00"
        first = events.record_event("probe.first", source.id, {}, occurred_at=timestamp)
        second = events.record_event("probe.second", source.id, {}, occurred_at=timestamp)

        tail = events.get_events(after_id=first.id)
        assert [e.id for e in tail] == [second.id]
    finally:
        db.close()


def test_default_schedules_survive_rebuild(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        scheduler = SchedulerEngine(db, events, MasterCritic(db))
        before = [row["name"] for row in scheduler.list_schedules()]
        assert before

        rebuild_state(db)
        after = [row["name"] for row in scheduler.list_schedules()]
        assert after == before
    finally:
        db.close()
