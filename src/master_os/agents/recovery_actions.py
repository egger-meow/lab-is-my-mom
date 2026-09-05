"""User-facing recovery actions for interrupted agent runs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from master_os.agents.packet import AgentJobPacket, WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id
from master_os.core.reducer import apply_event
from master_os.core.relations import RelationGraph


AgentExecutor = Callable[[Path, AgentJobPacket], dict[str, Any]]


class AgentRecoveryActions:
    """Inspect and resolve interrupted runs without destroying partial work.

    Crash detection and recovery *decisions* are intentionally separate. The
    supervisor may mark a stale run interrupted, but only an explicit recovery
    action chooses whether to resume, retry fresh, or abandon that work.
    """

    def __init__(
        self,
        db: MasterDatabase,
        events: EventStore,
        runtime: AgentRuntime,
        packet_builder: WorkPacketBuilder,
        relations: RelationGraph,
        repo_root: Path,
    ) -> None:
        self.db = db
        self.events = events
        self.runtime = runtime
        self.packet_builder = packet_builder
        self.relations = relations
        self.repo_root = repo_root.resolve()
        self.source = self.events.register_source(
            "user",
            "Agent Recovery Cockpit",
            "agent-recovery-cockpit",
            authority_class="user_explicit",
        )

    def list_interrupted(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """SELECT ar.*, t.title AS task_title
               FROM agent_runs ar
               LEFT JOIN tasks t ON t.id = ar.task_id
               WHERE ar.status = 'interrupted'
               ORDER BY COALESCE(ar.finished_at, ar.started_at, ar.created_at) DESC"""
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            workspace = Path(item["workspace"]).resolve() if item.get("workspace") else None
            item["workspace_exists"] = bool(workspace and workspace.exists())
            item["recommended_action"] = "resume" if self._workspace_has_partial_work(workspace) else "retry_fresh"
            result.append(item)
        return result

    def inspect(self, run_id: str) -> dict[str, Any]:
        row = self.db.fetchone("SELECT * FROM agent_runs WHERE id = ?", (run_id,))
        if not row:
            raise LookupError(f"Agent run not found: {run_id}")

        run = dict(row)
        task = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (run["task_id"],)) if run.get("task_id") else None
        workspace = Path(run["workspace"]).resolve() if run.get("workspace") else None
        files: list[str] = []
        if workspace and workspace.exists() and workspace.is_dir():
            for path in sorted(workspace.rglob("*")):
                if len(files) >= 200:
                    break
                if path.is_file() and path.name != ".git":
                    files.append(path.relative_to(workspace).as_posix())

        return {
            "run": run,
            "task": dict(task) if task else None,
            "workspace_exists": bool(workspace and workspace.exists()),
            "workspace_files": files,
            "recommended_action": "resume" if files else "retry_fresh",
        }

    def recover(
        self,
        run_id: str,
        action: str,
        *,
        executor: Optional[AgentExecutor] = None,
        note: str = "",
    ) -> dict[str, Any]:
        if action not in {"resume", "retry_fresh", "abandon"}:
            raise ValueError("action must be resume, retry_fresh, or abandon")

        row = self.db.fetchone("SELECT * FROM agent_runs WHERE id = ?", (run_id,))
        if not row:
            raise LookupError(f"Agent run not found: {run_id}")
        if row["status"] != "interrupted":
            raise RuntimeError(f"Agent run {run_id} is {row['status']}, not interrupted")
        if not row["task_id"]:
            raise RuntimeError(f"Interrupted run {run_id} has no task to recover")

        task = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (row["task_id"],))
        if not task:
            raise RuntimeError(f"Task {row['task_id']} no longer exists")

        if action in {"resume", "retry_fresh"} and executor is None:
            raise RuntimeError(f"No real {task['preferred_agent']} executor is configured")

        old_workspace = Path(row["workspace"]).resolve() if row["workspace"] else None
        if action == "resume" and (old_workspace is None or not old_workspace.exists()):
            raise RuntimeError("Cannot resume because the interrupted workspace no longer exists")

        self._record_recovery_event(
            "agent_run.recovery_started",
            run_id,
            action,
            note=note,
            extra={"task_id": row["task_id"], "final_status": "recovering"},
            dedup_key=f"agent-recovery-start:{run_id}:{action}",
        )

        if action == "abandon":
            self._record_recovery_event(
                "agent_run.recovery_decided",
                run_id,
                action,
                note=note,
                extra={"task_id": row["task_id"], "final_status": "abandoned"},
                dedup_key=f"agent-recovery-decision:{run_id}:{action}",
            )
            return {
                "run_id": run_id,
                "action": action,
                "new_run_id": None,
                "status": "abandoned",
            }

        if action == "resume":
            workspace = old_workspace
            branch = row["branch"] or f"agent/recover-{row['task_id'].lower()}"
        else:
            workspace = self.repo_root / ".master-os" / "worktrees" / (
                f"recovery-{row['task_id'].lower()}-{generate_id('WS-')[-8:].lower()}"
            )
            branch = None

        assert workspace is not None
        packet = self.packet_builder.build_packet(
            row["task_id"],
            workspace_path=str(workspace),
            branch=branch,
            repo_name=self.repo_root.name,
        )
        packet.context_notes.append(
            f"Recovery action {action} for interrupted run {run_id}. Preserve and inspect prior evidence before changing it."
        )

        try:
            result = self.runtime.dispatch_autonomous_job(
                packet,
                agent_type=task["preferred_agent"] or "codex",
                executor_func=executor,
                resume_existing_workspace=(action == "resume"),
            )
        except Exception as exc:
            # Recovery never leaves the old run stuck in a synthetic 'recovering'
            # state if a new run could not even be acquired/started.
            self._record_recovery_event(
                "agent_run.recovery_decided",
                run_id,
                action,
                note=note,
                extra={
                    "task_id": row["task_id"],
                    "final_status": "interrupted",
                    "error": str(exc),
                },
                dedup_key=f"agent-recovery-start-failed:{run_id}:{action}",
            )
            raise

        new_run_id = result["run_id"]
        self.relations.link("agent_run", new_run_id, "recovered_from", "agent_run", run_id)
        self._record_recovery_event(
            "agent_run.recovery_decided",
            run_id,
            action,
            note=note,
            extra={
                "task_id": row["task_id"],
                "new_run_id": new_run_id,
                "final_status": "superseded",
                "new_run_status": result["status"],
            },
            dedup_key=f"agent-recovery-decision:{run_id}:{action}",
        )
        return {
            "run_id": run_id,
            "action": action,
            "new_run_id": new_run_id,
            "status": result["status"],
            "task_status": result["task_status"],
            "error": result.get("error"),
            "artifacts": result.get("artifacts", []),
        }

    def _record_recovery_event(
        self,
        event_type: str,
        run_id: str,
        action: str,
        *,
        note: str,
        extra: dict[str, Any],
        dedup_key: str,
    ) -> None:
        """Append recovery intent plus a replayable terminal-state transition atomically."""
        payload = {"id": run_id, "action": action, "note": note, **extra}
        final_status = str(extra.get("final_status") or "").strip()
        try:
            self.db.execute("BEGIN IMMEDIATE")
            if event_type == "agent_run.recovery_started":
                current = self.db.fetchone("SELECT status FROM agent_runs WHERE id = ?", (run_id,))
                if not current or current["status"] != "interrupted":
                    raise RuntimeError(f"Agent run {run_id} is no longer available for recovery")

            recovery_event = self.events.record_event(
                event_type,
                self.source.id,
                payload,
                dedup_key=dedup_key,
                created_by="user_explicit",
                commit=False,
            )
            # recovery_event is audit/decision evidence. The existing replayable
            # agent_run.completed transition carries the materialized status so we do
            # not create a second ad-hoc state mutation path.
            _ = recovery_event

            if final_status:
                state_event = self.events.record_event(
                    "agent_run.completed",
                    self.source.id,
                    {
                        "id": run_id,
                        "status": final_status,
                        "exit_code": None,
                        "result_git_sha": None,
                        "result_artifact_id": None,
                        "failure_id": None,
                    },
                    dedup_key=f"{dedup_key}:state:{final_status}",
                    created_by="user_explicit",
                    commit=False,
                )
                apply_event(self.db, state_event, commit=False)

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _workspace_has_partial_work(workspace: Path | None) -> bool:
        if workspace is None or not workspace.exists() or not workspace.is_dir():
            return False
        return any(path.name != ".git" for path in workspace.iterdir())
