"""Regression tests for durable scheduler timing semantics."""
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event, rebuild_state
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


def test_legacy_default_advisor_schedule_is_migrated_canonically(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("scheduler", "Master Scheduler", "master-os-scheduler")
        legacy = events.record_event(
            "schedule.created",
            source.id,
            {
                "id": "SCH-LEGACY",
                "name": "Advisor Pre-Meeting Readiness & Pack",
                "trigger_type": "time_cron",
                "trigger_spec": {"day_of_week": "wed", "hour": 20, "minute": 0},
                "agent_role": "meeting_agent",
                "prompt_template": "legacy default",
                "enabled": True,
                "catch_up_policy": "run_once",
                "autonomy_policy": {"dispatch_local": True, "external_actions": "approval"},
                "last_run_at": None,
                "next_run_at": None,
                "created_at": "2026-09-01T00:00:00+00:00",
            },
            occurred_at="2026-09-01T00:00:00+00:00",
            dedup_key="legacy-default-schedule",
        )
        apply_event(db, legacy)

        scheduler = SchedulerEngine(db, events, MasterCritic(db))
        schedule = next(
            item for item in scheduler.list_schedules()
            if item["name"] == "Advisor Pre-Meeting Readiness & Pack"
        )
        assert schedule["trigger_type"] == "relative_meeting"
        assert schedule["trigger_spec"] == {"meeting_kind": "advisor", "offset_minutes": -720}
        assert db.fetchone(
            "SELECT COUNT(*) AS n FROM events WHERE dedup_key='schedule-migration:advisor-premeeting-relative:v1'"
        )["n"] == 1

        rebuild_state(db)
        replayed = next(
            item for item in scheduler.list_schedules()
            if item["name"] == "Advisor Pre-Meeting Readiness & Pack"
        )
        assert replayed["trigger_type"] == "relative_meeting"
        assert replayed["trigger_spec"] == {"meeting_kind": "advisor", "offset_minutes": -720}
    finally:
        db.close()
