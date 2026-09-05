"""Crash recovery for stale Master OS agent runs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event


class AgentRecovery:
    """Turn expired running leases into auditable interrupted runs.

    The workspace is deliberately never deleted or reset here. Recovery only changes
    durable run/task state so a human or later repair agent can inspect the exact
    interrupted worktree before deciding whether to resume, retry, or discard it.
    """

    def __init__(
        self,
        db: MasterDatabase,
        events: EventStore,
        *,
        stale_after_seconds: float = 180.0,
    ) -> None:
        if stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be positive")
        self.db = db
        self.events = events
        self.stale_after_seconds = float(stale_after_seconds)
        self.source = self.events.register_source(
            "system",
            "Agent Crash Recovery",
            "agent-crash-recovery",
        )

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _is_stale(self, row: Any, cutoff: datetime) -> bool:
        last_seen = (
            self._parse_timestamp(row["heartbeat_at"])
            or self._parse_timestamp(row["started_at"])
            or self._parse_timestamp(row["created_at"])
        )
        return last_seen is not None and last_seen <= cutoff

    def recover_stale_runs(self, now: datetime) -> list[dict[str, Any]]:
        if now.tzinfo is None:
            raise ValueError("Recovery clock must be timezone-aware")
        now = now.astimezone(timezone.utc)
        cutoff = now - timedelta(seconds=self.stale_after_seconds)

        candidates = self.db.fetchall(
            """SELECT * FROM agent_runs
               WHERE status = 'running'
               ORDER BY COALESCE(heartbeat_at, started_at, created_at) ASC"""
        )
        recovered: list[dict[str, Any]] = []

        for candidate in candidates:
            if not self._is_stale(candidate, cutoff):
                continue

            try:
                # Re-check under a SQLite write lock. A live heartbeat that landed
                # after the initial scan wins and prevents a false interruption.
                self.db.execute("BEGIN IMMEDIATE")
                current = self.db.fetchone(
                    "SELECT * FROM agent_runs WHERE id = ?",
                    (candidate["id"],),
                )
                if not current or current["status"] != "running" or not self._is_stale(current, cutoff):
                    self.db.rollback()
                    continue

                interrupt_event = self.events.record_event(
                    "agent_run.interrupted",
                    self.source.id,
                    {
                        "id": current["id"],
                        "task_id": current["task_id"],
                        "workspace": current["workspace"],
                        "branch": current["branch"],
                        "last_heartbeat": current["heartbeat_at"],
                        "reason": "stale_heartbeat",
                        "stale_after_seconds": self.stale_after_seconds,
                    },
                    occurred_at=now.isoformat(),
                    dedup_key=f"agent-run-interrupted:{current['id']}",
                    commit=False,
                )

                # Keep replay compatibility by materializing the terminal state via
                # the existing agent_run.completed reducer while retaining the more
                # precise interruption event above for audit/history.
                terminal_event = self.events.record_event(
                    "agent_run.completed",
                    self.source.id,
                    {
                        "id": current["id"],
                        "status": "interrupted",
                        "exit_code": None,
                        "result_git_sha": current["result_git_sha"],
                        "result_artifact_id": current["result_artifact_id"],
                        "failure_id": current["failure_id"],
                    },
                    occurred_at=now.isoformat(),
                    dedup_key=f"agent-run-terminal-interrupted:{current['id']}",
                    commit=False,
                )
                apply_event(self.db, terminal_event, commit=False)

                if current["task_id"]:
                    task_event = self.events.record_event(
                        "task.status_changed",
                        self.source.id,
                        {"id": current["task_id"], "status": "blocked"},
                        occurred_at=now.isoformat(),
                        dedup_key=f"agent-run-interrupted-task-blocked:{current['id']}",
                        commit=False,
                    )
                    apply_event(self.db, task_event, commit=False)

                # ``interrupt_event`` is intentionally append-only evidence. It has no
                # materialized reducer of its own; the terminal event above carries the
                # replayable state transition.
                _ = interrupt_event
                self.db.commit()
                recovered.append(
                    {
                        "run_id": current["id"],
                        "task_id": current["task_id"],
                        "workspace": current["workspace"],
                        "reason": "stale_heartbeat",
                    }
                )
            except Exception:
                self.db.rollback()
                raise

        return recovered
