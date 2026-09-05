"""Regression tests for durable scheduler timing semantics."""
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.scheduler.engine import SchedulerEngine


def _scheduler(tmp_path: Path) -> tuple[MasterDatabase, SchedulerEngine]:
    db = MasterDatabase(tmp_path / "master.db")
    events = EventStore(db)
    return db, SchedulerEngine(db, events, MasterCritic(db))


def test_advisor_premeeting_schedule_tracks_actual_meeting_time(tmp_path: Path):
    db, scheduler = _scheduler(tmp_path)
    try:
        schedule = next(
            item for item in scheduler.list_schedules()
            if item["name"] == "Advisor Pre-Meeting Readiness & Pack"
        )
        assert schedule["trigger_type"] == "relative_meeting"
        assert schedule["trigger_spec"] == {
            "meeting_kind": "advisor",
            "offset_minutes": -720,
        }
    finally:
        db.close()
