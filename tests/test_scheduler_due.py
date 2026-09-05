"""Regression tests for durable scheduler timing semantics."""
from datetime import datetime, timedelta, timezone
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


def test_relative_meeting_schedule_becomes_due_once_for_next_advisor_meeting(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        scheduler = SchedulerEngine(db, events, MasterCritic(db))
        source = events.register_source("test", "test", "meeting-due")
        meeting = events.record_event(
            "meeting.scheduled",
            source.id,
            {
                "id": "M-NEXT",
                "kind": "advisor",
                "title": "Advisor meeting",
                "scheduled_at": "2026-09-10T10:00:00+00:00",
            },
            occurred_at="2026-09-05T00:00:00+00:00",
        )
        apply_event(db, meeting)

        before = datetime(2026, 9, 9, 21, 59, tzinfo=timezone.utc)
        due_at = datetime(2026, 9, 9, 22, 0, tzinfo=timezone.utc)
        assert _named_due(scheduler.due_schedules(before), "Advisor Pre-Meeting Readiness & Pack") == []

        due = _named_due(scheduler.due_schedules(due_at), "Advisor Pre-Meeting Readiness & Pack")
        assert len(due) == 1
        assert due[0]["trigger_at"] == "2026-09-09T22:00:00+00:00"
        assert due[0]["context"]["meeting_id"] == "M-NEXT"

        _mark_triggered(db, events, due[0]["id"], due_at)
        assert _named_due(scheduler.due_schedules(due_at), "Advisor Pre-Meeting Readiness & Pack") == []
    finally:
        db.close()


def test_interval_schedule_catches_up_once_then_waits_for_next_interval(tmp_path: Path):
    db, scheduler = _scheduler(tmp_path)
    try:
        events = EventStore(db)
        schedule = next(item for item in scheduler.list_schedules() if item["name"] == "NCHC & API Resource Burn Watchdog")
        created_at = datetime.fromisoformat(schedule["created_at"])
        first_due_at = created_at + timedelta(minutes=60)

        assert _named_due(scheduler.due_schedules(first_due_at - timedelta(seconds=1)), schedule["name"]) == []
        due = _named_due(scheduler.due_schedules(first_due_at), schedule["name"])
        assert len(due) == 1
        assert due[0]["trigger_at"] == first_due_at.isoformat()

        _mark_triggered(db, events, schedule["id"], first_due_at)
        assert _named_due(scheduler.due_schedules(first_due_at + timedelta(minutes=59)), schedule["name"]) == []
        assert len(_named_due(scheduler.due_schedules(first_due_at + timedelta(minutes=60)), schedule["name"])) == 1
    finally:
        db.close()


def test_weekly_time_cron_is_evaluated_in_taipei_timezone(tmp_path: Path):
    db, scheduler = _scheduler(tmp_path)
    try:
        name = "Weekly Research Progress & Critic"
        before = datetime(2026, 9, 6, 11, 59, tzinfo=timezone.utc)
        occurrence = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)  # Sunday 20:00 Asia/Taipei

        assert _named_due(scheduler.due_schedules(before), name) == []
        due = _named_due(scheduler.due_schedules(occurrence), name)
        assert len(due) == 1
        assert due[0]["trigger_at"] == occurrence.isoformat()
    finally:
        db.close()


def test_event_schedule_fires_once_for_new_matching_event(tmp_path: Path):
    db, scheduler = _scheduler(tmp_path)
    try:
        events = EventStore(db)
        name = "Advisor Post-Meeting Digest to Slack"
        schedule = next(item for item in scheduler.list_schedules() if item["name"] == name)
        created_at = datetime.fromisoformat(schedule["created_at"])
        before = created_at + timedelta(seconds=30)
        event_at = created_at + timedelta(minutes=1)
        assert _named_due(scheduler.due_schedules(before), name) == []

        source = events.register_source("test", "test", "meeting-event")
        completed = events.record_event(
            "meeting.completed",
            source.id,
            {"id": "M-DONE"},
            occurred_at=event_at.isoformat(),
        )
        due = _named_due(scheduler.due_schedules(event_at), name)
        assert len(due) == 1
        assert due[0]["context"]["event_id"] == completed.id
        assert due[0]["context"]["event_type"] == "meeting.completed"

        _mark_triggered(db, events, due[0]["id"], event_at)
        assert _named_due(scheduler.due_schedules(event_at + timedelta(minutes=1)), name) == []
    finally:
        db.close()


def _mark_triggered(db: MasterDatabase, events: EventStore, schedule_id: str, when: datetime) -> None:
    scheduler_source = events.register_source("scheduler", "Master Scheduler", "master-os-scheduler")
    event = events.record_event(
        "schedule.triggered",
        scheduler_source.id,
        {"id": schedule_id, "last_run_at": when.isoformat()},
        occurred_at=when.isoformat(),
    )
    apply_event(db, event)


def _named_due(items: list[dict], name: str) -> list[dict]:
    return [item for item in items if item["name"] == name]
