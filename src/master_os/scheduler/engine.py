"""AI Scheduler Engine for Master OS: durable, data-driven agent routines."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

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
        """Return enabled routines whose current trigger occurrence has not run.

        This first durable timing primitive intentionally starts with
        ``relative_meeting``. Other trigger families are added explicitly rather
        than pretending that a stored schedule is already an executing daemon.
        """
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("Scheduler clock must be timezone-aware")
        current = current.astimezone(timezone.utc)

        due: list[dict[str, Any]] = []
        rows = self.db.fetchall("SELECT * FROM schedules WHERE enabled = 1 ORDER BY created_at ASC")
        for row in rows:
            if row["trigger_type"] != "relative_meeting":
                continue
            item = self._relative_meeting_due(row, current)
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
        if current < trigger_at:
            return None

        last_run_at = self._parse_time(row["last_run_at"]) if row["last_run_at"] else None
        if last_run_at is not None and last_run_at >= trigger_at:
            return None

        item = self._schedule_payload_from_row(row)
        item["trigger_at"] = trigger_at.isoformat()
        item["context"] = {
            "meeting_id": meeting["id"],
            "meeting_kind": meeting["kind"],
            "meeting_title": meeting["title"],
            "scheduled_at": meeting["scheduled_at"],
        }
        return item

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def trigger_routine(self, schedule_name: str) -> dict[str, Any]:
        """Execute a routine and record the trigger in canonical history."""
        row = self.db.fetchone("SELECT * FROM schedules WHERE name = ? AND enabled = 1", (schedule_name,))
        if not row:
            raise ValueError(f"Enabled schedule not found: {schedule_name}")

        now = utc_now()
        role = row["agent_role"]
        result: dict[str, Any] = {"schedule": schedule_name, "executed_at": now, "status": "ok"}

        if role == "critic":
            report = self.critic.evaluate_health()
            result["health_report"] = {
                "velocity": report.research_velocity,
                "warning": report.fake_progress_warning,
                "message": report.warning_message,
                "burn_warnings": report.resource_burn_warnings,
            }

        source = self.events.register_source("scheduler", "Master Scheduler", "master-os-scheduler")
        event = self.events.record_event(
            "schedule.triggered",
            source.id,
            {"id": row["id"], "last_run_at": now},
        )
        apply_event(self.db, event)
        return result
