"""Supervisor runtime tests: one durable tick instead of a decorative scheduler."""
from datetime import datetime, timezone
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event
from master_os.scheduler.engine import SchedulerEngine
from master_os.supervisor.runtime import MasterSupervisor


def test_supervisor_tick_syncs_sources_executes_due_work_and_heartbeats(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        scheduler = SchedulerEngine(db, events, MasterCritic(db))
        source = events.register_source("test", "test", "supervisor-meeting")
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

        handled: list[str] = []
        slack_calls: list[str] = []

        def meeting_handler(item: dict) -> dict:
            handled.append(item["context"]["meeting_id"])
            return {"status": "ok", "artifact": "meeting-pack"}

        def slack_sync() -> dict:
            slack_calls.append("lab-general")
            return {"ingested": 2}

        supervisor = MasterSupervisor(
            db,
            scheduler,
            routine_handlers={"meeting_agent": meeting_handler},
            source_syncers={"slack:lab-general": slack_sync},
        )
        now = datetime(2026, 9, 9, 22, 0, tzinfo=timezone.utc)
        first = supervisor.run_once(now)

        assert first["status"] == "ok"
        assert handled == ["M-NEXT"]
        assert slack_calls == ["lab-general"]
        assert first["sources"]["slack:lab-general"]["ingested"] == 2

        health = db.fetchone("SELECT * FROM system_health WHERE subsystem='supervisor'")
        assert health is not None
        assert health["status"] == "ok"
        assert health["last_heartbeat"] == now.isoformat()

        schedule = db.fetchone("SELECT * FROM schedules WHERE name='Advisor Pre-Meeting Readiness & Pack'")
        assert schedule["last_run_at"] == now.isoformat()

        second = supervisor.run_once(now)
        assert second["status"] == "ok"
        assert handled == ["M-NEXT"]
        assert slack_calls == ["lab-general", "lab-general"]
    finally:
        db.close()


def test_supervisor_does_not_acknowledge_failed_routine(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        scheduler = SchedulerEngine(db, events, MasterCritic(db))
        source = events.register_source("test", "test", "failed-supervisor-meeting")
        meeting = events.record_event(
            "meeting.scheduled",
            source.id,
            {
                "id": "M-FAIL",
                "kind": "advisor",
                "title": "Advisor meeting",
                "scheduled_at": "2026-09-10T10:00:00+00:00",
            },
            occurred_at="2026-09-05T00:00:00+00:00",
        )
        apply_event(db, meeting)

        def failing_handler(_: dict) -> dict:
            raise RuntimeError("agent unavailable")

        supervisor = MasterSupervisor(db, scheduler, routine_handlers={"meeting_agent": failing_handler})
        now = datetime(2026, 9, 9, 22, 0, tzinfo=timezone.utc)
        report = supervisor.run_once(now)

        assert report["status"] == "warning"
        failed = next(item for item in report["routines"] if item["name"] == "Advisor Pre-Meeting Readiness & Pack")
        assert failed["status"] == "failed"
        schedule = db.fetchone("SELECT * FROM schedules WHERE name='Advisor Pre-Meeting Readiness & Pack'")
        assert schedule["last_run_at"] is None
    finally:
        db.close()
