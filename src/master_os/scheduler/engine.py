"""AI Scheduler Engine for Master OS: durable, data-driven agent routines."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id, utc_now
from master_os.core.reducer import apply_event
from master_os.lab.protocol import create_default_lab_schedules


_ADVISOR_PREP_NAME = "Advisor Pre-Meeting Readiness & Pack"
_LEGACY_ADVISOR_PREP_TRIGGER = {
    "trigger_type": "time_cron",
    "trigger_spec": {"day_of_week": "wed", "hour": 20, "minute": 0},
}
_WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


class SchedulerEngine:
    """Orchestrates scheduled routines while keeping schedule state replayable."""

    def __init__(self, db: MasterDatabase, events: EventStore, critic: MasterCritic) -> None:
        self.db = db
        self.events = events
        self.critic = critic
        self._ensure_event_backed_schedules()

    def _schedule_payload_from_row(self, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "trigger_type": row["trigger_type"],
            "trigger_spec": json.loads(row["trigger_spec_json"]),
            "agent_role": row["agent_role"],
            "prompt_template": row["prompt_template"],
            "enabled": bool(row["enabled"]),
            "catch_up_policy": row["catch_up_policy"],
            "autonomy_policy": json.loads(row["autonomy_policy_json"]),
            "last_run_at": row["last_run_at"],
            "next_run_at": row["next_run_at"],
            "created_at": row["created_at"],
        }

    def _ensure_event_backed_schedules(self) -> None:
        """Seed defaults, backfill legacy rows, and apply narrow built-in migrations.

        Older Master OS builds inserted schedules directly. On first startup after
        this migration, each existing row is captured once as ``schedule.created``
        so ``rebuild-state`` cannot erase user-visible scheduler configuration.

        Built-in migrations are intentionally narrow. We only rewrite an exact
        historical default shape, never an arbitrary user-customized schedule.
        """
        source = self.events.register_source("scheduler", "Master Scheduler", "master-os-scheduler")
        existing = self.db.fetchall("SELECT * FROM schedules ORDER BY created_at ASC")

        if existing:
            for row in existing:
                event = self.events.record_event(
                    "schedule.created",
                    source.id,
                    self._schedule_payload_from_row(row),
                    dedup_key=f"schedule-bootstrap:{row['id']}",
                )
                apply_event(self.db, event)
            self._migrate_legacy_default_schedules(source.id)
            return

        now = utc_now()
        for spec in create_default_lab_schedules():
            sid = generate_id("SCH-")
            payload = {
                "id": sid,
                "name": spec["name"],
                "trigger_type": spec["trigger_type"],
                "trigger_spec": spec["trigger_spec"],
                "agent_role": spec["agent_role"],
                "prompt_template": spec["prompt_template"],
                "enabled": True,
                "catch_up_policy": spec.get("catch_up_policy", "run_once"),
                "autonomy_policy": spec["autonomy_policy"],
                "last_run_at": None,
                "next_run_at": None,
                "created_at": now,
            }
            event = self.events.record_event(
                "schedule.created",
                source.id,
                payload,
                dedup_key=f"default-schedule:{spec['name']}",
            )
            apply_event(self.db, event)

    def _migrate_legacy_default_schedules(self, source_id: str) -> None:
        """Upgrade only recognized historical defaults through canonical events."""
        row = self.db.fetchone("SELECT * FROM schedules WHERE name = ?", (_ADVISOR_PREP_NAME,))
        if not row:
            return

        trigger_spec = json.loads(row["trigger_spec_json"])
        if (
            row["trigger_type"] != _LEGACY_ADVISOR_PREP_TRIGGER["trigger_type"]
            or trigger_spec != _LEGACY_ADVISOR_PREP_TRIGGER["trigger_spec"]
        ):
            return

        new_default = next(
            spec for spec in create_default_lab_schedules()
            if spec["name"] == _ADVISOR_PREP_NAME
        )
        payload = self._schedule_payload_from_row(row)
        payload["trigger_type"] = new_default["trigger_type"]
        payload["trigger_spec"] = new_default["trigger_spec"]
        event = self.events.record_event(
            "schedule.created",
            source_id,
            payload,
            dedup_key="schedule-migration:advisor-premeeting-relative:v1",
            created_by="scheduler_migration",
        )
        apply_event(self.db, event)

    def list_schedules(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall("SELECT * FROM schedules ORDER BY created_at ASC")
        return [self._schedule_payload_from_row(r) for r in rows]

    def due_schedules(self, now: Optional[datetime] = None) -> list[dict[str, Any]]:
        """Return enabled routines whose latest trigger occurrence has not run."""
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("Scheduler clock must be timezone-aware")
        current = current.astimezone(timezone.utc)

        due: list[dict[str, Any]] = []
        rows = self.db.fetchall("SELECT * FROM schedules WHERE enabled = 1 ORDER BY created_at ASC")
        for row in rows:
            trigger_type = row["trigger_type"]
            if trigger_type == "relative_meeting":
                item = self._relative_meeting_due(row, current)
            elif trigger_type == "interval":
                item = self._interval_due(row, current)
            elif trigger_type == "time_cron":
                item = self._weekly_cron_due(row, current)
            elif trigger_type == "event":
                item = self._event_due(row, current)
            else:
                item = None
            if item is not None:
                due.append(item)
        return due

    def _relative_meeting_due(self, row: Any, current: datetime) -> Optional[dict[str, Any]]:
        spec = json.loads(row["trigger_spec_json"])
        meeting_kind = str(spec.get("meeting_kind") or "").strip()
        if not meeting_kind:
            return None

        meeting = self.db.fetchone(
            """SELECT * FROM meetings
               WHERE kind = ? AND status = 'scheduled' AND scheduled_at > ?
               ORDER BY scheduled_at ASC LIMIT 1""",
            (meeting_kind, current.isoformat()),
        )
        if not meeting:
            return None

        meeting_at = self._parse_time(meeting["scheduled_at"])
        offset_minutes = int(spec.get("offset_minutes", 0))
        trigger_at = meeting_at + timedelta(minutes=offset_minutes)
        if current < trigger_at or self._already_ran(row, trigger_at):
            return None

        return self._due_item(
            row,
            trigger_at,
            {
                "meeting_id": meeting["id"],
                "meeting_kind": meeting["kind"],
                "meeting_title": meeting["title"],
                "scheduled_at": meeting["scheduled_at"],
            },
        )

    def _interval_due(self, row: Any, current: datetime) -> Optional[dict[str, Any]]:
        spec = json.loads(row["trigger_spec_json"])
        interval_minutes = int(spec.get("interval_minutes", 0))
        if interval_minutes <= 0:
            return None
        base = self._parse_time(row["last_run_at"] or row["created_at"])
        trigger_at = base + timedelta(minutes=interval_minutes)
        if current < trigger_at:
            return None
        return self._due_item(row, trigger_at, {})

    def _weekly_cron_due(self, row: Any, current: datetime) -> Optional[dict[str, Any]]:
        spec = json.loads(row["trigger_spec_json"])
        weekday_name = str(spec.get("day_of_week") or "").lower()
        if weekday_name not in _WEEKDAYS:
            return None
        hour = int(spec.get("hour", 0))
        minute = int(spec.get("minute", 0))
        zone = ZoneInfo(str(spec.get("timezone") or "Asia/Taipei"))
        local_now = current.astimezone(zone)
        days_back = (local_now.weekday() - _WEEKDAYS[weekday_name]) % 7
        occurrence_date = (local_now - timedelta(days=days_back)).date()
        occurrence_local = datetime(
            occurrence_date.year,
            occurrence_date.month,
            occurrence_date.day,
            hour,
            minute,
            tzinfo=zone,
        )
        if occurrence_local > local_now:
            occurrence_local -= timedelta(days=7)
        trigger_at = occurrence_local.astimezone(timezone.utc)
        created_at = self._parse_time(row["created_at"])
        if trigger_at < created_at or self._already_ran(row, trigger_at):
            return None
        return self._due_item(row, trigger_at, {})

    def _event_due(self, row: Any, current: datetime) -> Optional[dict[str, Any]]:
        spec = json.loads(row["trigger_spec_json"])
        event_type = str(spec.get("event_type") or "").strip()
        if not event_type:
            return None
        since = self._parse_time(row["last_run_at"] or row["created_at"]).isoformat()
        event = self.db.fetchone(
            """SELECT * FROM events
               WHERE event_type = ? AND occurred_at > ? AND occurred_at <= ?
               ORDER BY occurred_at ASC, rowid ASC LIMIT 1""",
            (event_type, since, current.isoformat()),
        )
        if not event:
            return None
        trigger_at = self._parse_time(event["occurred_at"])
        return self._due_item(
            row,
            trigger_at,
            {
                "event_id": event["id"],
                "event_type": event["event_type"],
                "event_payload": json.loads(event["payload_json"]),
            },
        )

    def _already_ran(self, row: Any, trigger_at: datetime) -> bool:
        if not row["last_run_at"]:
            return False
        return self._parse_time(row["last_run_at"]) >= trigger_at

    def _due_item(self, row: Any, trigger_at: datetime, context: dict[str, Any]) -> dict[str, Any]:
        item = self._schedule_payload_from_row(row)
        item["trigger_at"] = trigger_at.astimezone(timezone.utc).isoformat()
        item["context"] = context
        return item

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def mark_triggered(
        self,
        schedule_id: str,
        executed_at: datetime,
        *,
        trigger_at: Optional[str] = None,
    ) -> None:
        """Durably acknowledge one successful schedule occurrence."""
        if executed_at.tzinfo is None:
            raise ValueError("Scheduler execution time must be timezone-aware")
        executed_iso = executed_at.astimezone(timezone.utc).isoformat()
        occurrence = trigger_at or executed_iso
        source = self.events.register_source("scheduler", "Master Scheduler", "master-os-scheduler")
        event = self.events.record_event(
            "schedule.triggered",
            source.id,
            {"id": schedule_id, "last_run_at": executed_iso, "trigger_at": occurrence},
            occurred_at=executed_iso,
            dedup_key=f"schedule-trigger:{schedule_id}:{occurrence}",
        )
        apply_event(self.db, event)

    def trigger_routine(self, schedule_name: str) -> dict[str, Any]:
        """Execute a built-in routine and record the trigger in canonical history."""
        row = self.db.fetchone("SELECT * FROM schedules WHERE name = ? AND enabled = 1", (schedule_name,))
        if not row:
            raise ValueError(f"Enabled schedule not found: {schedule_name}")

        role = row["agent_role"]
        if role != "critic":
            raise RuntimeError(
                f"Schedule {schedule_name!r} requires a configured {role!r} runtime handler; refusing a fake success."
            )

        report = self.critic.evaluate_health()
        now = datetime.now(timezone.utc)
        result: dict[str, Any] = {
            "schedule": schedule_name,
            "executed_at": now.isoformat(),
            "status": "ok",
            "health_report": {
                "velocity": report.research_velocity,
                "warning": report.fake_progress_warning,
                "message": report.warning_message,
                "burn_warnings": report.resource_burn_warnings,
            },
        }
        self.mark_triggered(row["id"], now)
        return result
