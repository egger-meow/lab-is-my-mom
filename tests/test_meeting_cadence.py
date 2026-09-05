from datetime import datetime, timezone
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.core.assertions import AssertionResolver
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import AuthorityLevel
from master_os.lab.cadence import next_weekly_occurrence, occurrence_id
from master_os.scheduler.engine import SchedulerEngine


def test_next_weekly_occurrence_uses_taipei_local_time():
    spec = {"day_of_week": "wed", "start_time": "14:00", "timezone": "Asia/Taipei"}
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    occurrence = next_weekly_occurrence(spec, now)
    assert occurrence.isoformat() == "2026-09-09T06:00:00+00:00"
    assert occurrence_id("advisor", occurrence, spec) == "M-ADV-20260909"


def test_advisor_readiness_uses_weekly_assertion_without_materialized_meeting(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        assertions = AssertionResolver(db, events)
        assertions.assert_field(
            "meeting_routine",
            "advisor",
            "weekly_spec",
            {"day_of_week": "wed", "start_time": "14:00", "timezone": "Asia/Taipei"},
            authority=AuthorityLevel.USER_EXPLICIT,
            confidence=1.0,
        )
        scheduler = SchedulerEngine(db, events, MasterCritic(db))
        assert db.fetchone("SELECT COUNT(*) AS n FROM meetings")["n"] == 0

        before = datetime(2026, 9, 8, 17, 59, tzinfo=timezone.utc)
        due_at = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)
        name = "Advisor Pre-Meeting Readiness & Pack"
        assert [d for d in scheduler.due_schedules(before) if d["name"] == name] == []
        due = [d for d in scheduler.due_schedules(due_at) if d["name"] == name]
        assert len(due) == 1
        assert due[0]["context"]["meeting_id"] == "M-ADV-20260909"
        assert due[0]["context"]["recurring"] is True
        assert due[0]["context"]["scheduled_at"] == "2026-09-09T06:00:00+00:00"
    finally:
        db.close()
