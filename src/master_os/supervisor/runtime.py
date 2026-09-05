"""Long-lived supervisor loop for Master OS."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from master_os.core.database import MasterDatabase
from master_os.scheduler.engine import SchedulerEngine


RoutineHandler = Callable[[dict[str, Any]], dict[str, Any]]
SourceSyncer = Callable[[], dict[str, Any]]
RecoveryHandler = Callable[[datetime], list[dict[str, Any]]]
AgentPump = Callable[[], dict[str, Any]]
MaintenanceHandler = Callable[[datetime], dict[str, Any]]


class MasterSupervisor:
    """Continuously collect, schedule, recover, dispatch, maintain, and heartbeat."""

    def __init__(
        self,
        db: MasterDatabase,
        scheduler: SchedulerEngine,
        *,
        routine_handlers: Optional[dict[str, RoutineHandler]] = None,
        source_syncers: Optional[dict[str, SourceSyncer]] = None,
        recovery_handler: Optional[RecoveryHandler] = None,
        agent_pump: Optional[AgentPump] = None,
        maintenance_handlers: Optional[dict[str, MaintenanceHandler]] = None,
        poll_seconds: float = 60.0,
    ) -> None:
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        self.db = db
        self.scheduler = scheduler
        self.routine_handlers = dict(routine_handlers or {})
        self.source_syncers = dict(source_syncers or {})
        self.recovery_handler = recovery_handler
        self.agent_pump = agent_pump
        self.maintenance_handlers = dict(maintenance_handlers or {})
        self.poll_seconds = float(poll_seconds)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def run_once(self, now: Optional[datetime] = None) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("Supervisor clock must be timezone-aware")
        current = current.astimezone(timezone.utc)

        recoveries: list[dict[str, Any]] = []
        source_results: dict[str, dict[str, Any]] = {}
        routine_results: list[dict[str, Any]] = []
        maintenance_results: dict[str, dict[str, Any]] = {}
        agent_queue: dict[str, Any] = {}
        warnings: list[str] = []

        if self.recovery_handler is not None:
            try:
                recoveries = self.recovery_handler(current)
            except Exception as exc:
                warnings.append(f"agent recovery: {exc}")

        for name, syncer in self.source_syncers.items():
            try:
                source_results[name] = syncer()
            except Exception as exc:
                source_results[name] = {"status": "failed", "error": str(exc)}
                warnings.append(f"source {name}: {exc}")

        try:
            due = self.scheduler.due_schedules(current)
        except Exception as exc:
            warnings.append(f"scheduler due detection: {exc}")
            due = []

        for item in due:
            role = item["agent_role"]
            try:
                handler = self.routine_handlers.get(role)
                if handler is not None:
                    result = handler(item)
                elif role == "critic":
                    result = self._run_critic()
                else:
                    routine_results.append(
                        {
                            "name": item["name"],
                            "agent_role": role,
                            "status": "blocked",
                            "error": f"no runtime handler configured for {role}",
                        }
                    )
                    warnings.append(f"routine {item['name']}: no handler for {role}")
                    continue

                self.scheduler.mark_triggered(
                    item["id"],
                    current,
                    trigger_at=item.get("trigger_at"),
                )
                routine_results.append(
                    {
                        "name": item["name"],
                        "agent_role": role,
                        "status": "ok",
                        "result": result,
                    }
                )
            except Exception as exc:
                routine_results.append(
                    {
                        "name": item["name"],
                        "agent_role": role,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                warnings.append(f"routine {item['name']}: {exc}")

        # Pump after routines so a scheduled routine can enqueue work and have it
        # submitted in the same tick. pump_once is non-blocking by contract.
        if self.agent_pump is not None:
            try:
                agent_queue = self.agent_pump()
            except Exception as exc:
                agent_queue = {"status": "failed", "error": str(exc)}
                warnings.append(f"agent queue: {exc}")

        for name, handler in self.maintenance_handlers.items():
            try:
                maintenance_results[name] = handler(current)
            except Exception as exc:
                maintenance_results[name] = {"status": "failed", "error": str(exc)}
                warnings.append(f"maintenance {name}: {exc}")

        status = "warning" if warnings else "ok"
        details = {
            "recoveries": recoveries,
            "sources": source_results,
            "routines": routine_results,
            "agent_queue": agent_queue,
            "maintenance": maintenance_results,
            "warnings": warnings,
        }
        self._heartbeat(status, current, details)
        return {
            "status": status,
            "checked_at": current.isoformat(),
            "recoveries": recoveries,
            "sources": source_results,
            "routines": routine_results,
            "agent_queue": agent_queue,
            "maintenance": maintenance_results,
            "warnings": warnings,
        }

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="master-os-supervisor", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as exc:
                now = datetime.now(timezone.utc)
                self._heartbeat(
                    "warning",
                    now,
                    {
                        "warnings": [f"supervisor loop: {exc}"],
                        "recoveries": [],
                        "sources": {},
                        "routines": [],
                        "agent_queue": {},
                        "maintenance": {},
                    },
                )
            self._stop_event.wait(self.poll_seconds)

    def _run_critic(self) -> dict[str, Any]:
        report = self.scheduler.critic.evaluate_health()
        return {
            "velocity": report.research_velocity,
            "warning": report.fake_progress_warning,
            "message": report.warning_message,
            "burn_warnings": report.resource_burn_warnings,
        }

    def _heartbeat(self, status: str, now: datetime, details: dict[str, Any]) -> None:
        warning_text = "; ".join(details.get("warnings", []))
        message = warning_text if warning_text else "Supervisor tick completed successfully"
        self.db.execute(
            """INSERT INTO system_health (subsystem, status, last_heartbeat, message, details_json)
               VALUES ('supervisor', ?, ?, ?, ?)
               ON CONFLICT(subsystem) DO UPDATE SET
               status=excluded.status,
               last_heartbeat=excluded.last_heartbeat,
               message=excluded.message,
               details_json=excluded.details_json""",
            (status, now.isoformat(), message, json.dumps(details, ensure_ascii=False)),
        )
        self.db.commit()
