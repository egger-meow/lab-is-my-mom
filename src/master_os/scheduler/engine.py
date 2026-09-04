"""AI Scheduler Engine for Master OS: Dynamic, data-driven agent routines."""
from __future__ import annotations

import json
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id, utc_now
from master_os.lab.protocol import create_default_lab_schedules
from master_os.agents.critic import MasterCritic


class SchedulerEngine:
    """Orchestrates scheduled agent routines, catch-up executions, and autonomous triggers."""

    def __init__(self, db: MasterDatabase, events: EventStore, critic: MasterCritic) -> None:
        self.db = db
        self.events = events
        self.critic = critic
        self._ensure_default_schedules()

    def _ensure_default_schedules(self) -> None:
        """Seed default lab schedules if none exist."""
        existing = self.db.fetchall("SELECT id FROM schedules LIMIT 1")
        if not existing:
            defaults = create_default_lab_schedules()
            now = utc_now()
            for s in defaults:
                sid = generate_id("SCH-")
                self.db.execute(
                    """INSERT INTO schedules (id, name, trigger_type, trigger_spec_json, agent_role,
                                             prompt_template, enabled, catch_up_policy, autonomy_policy_json,
                                             created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 1, 'run_once', ?, ?, ?)""",
                    (sid, s["name"], s["trigger_type"], json.dumps(s["trigger_spec"], ensure_ascii=False),
                     s["agent_role"], s["prompt_template"], json.dumps(s["autonomy_policy"], ensure_ascii=False),
                     now, now)
                )
            self.db.commit()

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
                "autonomy_policy": json.loads(r["autonomy_policy_json"]),
                "last_run_at": r["last_run_at"],
                "next_run_at": r["next_run_at"],
            }
            for r in rows
        ]

    def trigger_routine(self, schedule_name: str) -> dict[str, Any]:
        """Execute a scheduled routine dynamically."""
        row = self.db.fetchone("SELECT * FROM schedules WHERE name = ?", (schedule_name,))
        if not row:
            raise ValueError(f"Schedule not found: {schedule_name}")

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

        # Update last_run_at
        self.db.execute("UPDATE schedules SET last_run_at = ?, updated_at = ? WHERE id = ?", (now, now, row["id"]))
        self.db.commit()

        return result
