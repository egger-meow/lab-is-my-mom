"""AI Scheduler Engine for Master OS: durable, data-driven agent routines."""
from __future__ import annotations

import json
from typing import Any

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id, utc_now
from master_os.core.reducer import apply_event
from master_os.lab.protocol import create_default_lab_schedules


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
        """Seed defaults or backfill legacy schedule rows into canonical history.

        Older Master OS builds inserted schedules directly. On first startup after
        this migration, each existing row is captured once as ``schedule.created``
        so ``rebuild-state`` cannot erase user-visible scheduler configuration.
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

    def list_schedules(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall("SELECT * FROM schedules ORDER BY created_at ASC")
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "trigger_type": r["trigger_type"],
                "trigger_spec": json.loads(r["trigger_spec_json"]),
                "agent_role": r["agent_role"],
                "prompt_template": r["prompt_template"],
                "enabled": bool(r["enabled"]),
                "catch_up_policy": r["catch_up_policy"],
                "autonomy_policy": json.loads(r["autonomy_policy_json"]),
                "last_run_at": r["last_run_at"],
                "next_run_at": r["next_run_at"],
            }
            for r in rows
        ]

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
