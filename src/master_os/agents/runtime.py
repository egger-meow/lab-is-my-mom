"""Agent Runtime for authorized local execution in isolated workspaces."""
from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from master_os.agents.packet import AgentJobPacket
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id
from master_os.core.reducer import apply_event


class AgentRuntime:
    """Manage isolated agent runs and deterministic post-run checks.

    A missing executor is a configuration error, never a successful dry-run.
    Production must inject an actual Codex/Antigravity adapter.
    """

    def __init__(
        self,
        db: MasterDatabase,
        event_store: EventStore,
        artifact_registry: ArtifactRegistry,
        repo_root: Path,
    ) -> None:
        self.db = db
        self.events = event_store
        self.commands = DomainCommandBus(db, event_store)
        self.artifacts = artifact_registry
        self.repo_root = repo_root.resolve()
        self.worktrees_dir = self.repo_root / ".master-os" / "worktrees"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        self.heartbeat_interval_seconds = 30.0
        self.source = self.events.register_source("agent_runner", "Agent Runner", "master-os-agent-runner")

    def _prepare_workspace(self, packet: AgentJobPacket) -> Path:
        """Prepare a fresh workspace without silently degrading isolation."""
        path = Path(packet.workspace_path).resolve()
        if path.exists() and any(path.iterdir()):
            # Existing non-empty workspaces may contain interrupted work. Never delete
            # them implicitly because that destroys recovery evidence.
            raise RuntimeError(f"Agent workspace already exists and is non-empty: {path}")

        if (self.repo_root / ".git").exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["git", "worktree", "add", "-b", packet.branch, str(path), "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"git worktree creation failed: {result.stderr.strip()}")
        else:
            # Non-git sandboxes are allowed for tests/local tools only.
            path.mkdir(parents=True, exist_ok=True)
        return path

    def _resume_workspace(self, packet: AgentJobPacket) -> Path:
        """Reuse an interrupted workspace only when recovery explicitly requests it."""
        path = Path(packet.workspace_path).resolve()
        if not path.exists() or not path.is_dir():
            raise RuntimeError(f"Interrupted agent workspace no longer exists: {path}")
        return path

    def _claim_task_run(
        self,
        run_id: str,
        packet: AgentJobPacket,
        agent_type: str,
        base_sha: Optional[str],
        *,
        require_queued: bool = False,
    ) -> None:
        """Atomically claim a direct or prequeued run before execution."""
        source = self.events.register_source(
            "agent_runner", f"{agent_type}_runner", f"runner-{agent_type}"
        )
        try:
            self.db.execute("BEGIN IMMEDIATE")
            packet_artifact_id: Optional[str] = None
            if require_queued:
                queued = self.db.fetchone("SELECT * FROM agent_runs WHERE id = ?", (run_id,))
                if not queued or queued["status"] != "queued":
                    state = queued["status"] if queued else "missing"
                    raise RuntimeError(f"Queued run {run_id} cannot be claimed; current state is {state}")
                if queued["task_id"] != packet.task_id:
                    raise RuntimeError(f"Queued run {run_id} task identity no longer matches its packet")
                packet_artifact_id = queued["packet_artifact_id"]
                active = self.db.fetchone(
                    """SELECT id FROM agent_runs
                       WHERE task_id = ? AND id <> ? AND status = 'running'
                       ORDER BY started_at DESC LIMIT 1""",
                    (packet.task_id, run_id),
                )
            else:
                active = self.db.fetchone(
                    """SELECT id FROM agent_runs
                       WHERE task_id = ? AND status IN ('queued', 'running')
                       ORDER BY created_at DESC LIMIT 1""",
                    (packet.task_id,),
                )
            if active:
                raise RuntimeError(
                    f"Task {packet.task_id} already has active agent run {active['id']}; lease is held"
                )

            start_event = self.events.record_event(
                event_type="agent_run.started",
                source_id=source.id,
                payload={
                    "id": run_id,
                    "agent_type": agent_type,
                    "job_type": "implementation",
                    "task_id": packet.task_id,
                    "workspace": str(Path(packet.workspace_path).resolve()),
                    "branch": packet.branch,
                    "base_git_sha": base_sha,
                    "packet_artifact_id": packet_artifact_id,
                },
                dedup_key=f"agent-run-started:{run_id}",
                commit=False,
            )
            apply_event(self.db, start_event, commit=False)
            task_event = self.events.record_event(
                "task.status_changed",
                source.id,
                {"id": packet.task_id, "status": "in_progress"},
                dedup_key=f"agent-run-task-started:{run_id}",
                commit=False,
            )
            apply_event(self.db, task_event, commit=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _heartbeat_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _publish_heartbeat(self, db: MasterDatabase, run_id: str) -> None:
        db.execute(
            "UPDATE agent_runs SET heartbeat_at = ? WHERE id = ? AND status = 'running'",
            (self._heartbeat_timestamp(), run_id),
        )
        db.commit()

    def _start_heartbeat(self, run_id: str) -> tuple[threading.Event, threading.Thread]:
        """Start a lease heartbeat without sharing the dispatch SQLite connection."""
        if self.heartbeat_interval_seconds <= 0:
            raise ValueError("heartbeat_interval_seconds must be positive")

        self._publish_heartbeat(self.db, run_id)
        stop_event = threading.Event()

        def heartbeat_loop() -> None:
            heartbeat_db = MasterDatabase(self.db.db_path)
            try:
                while not stop_event.wait(self.heartbeat_interval_seconds):
                    self._publish_heartbeat(heartbeat_db, run_id)
            finally:
                heartbeat_db.close()

        thread = threading.Thread(
            target=heartbeat_loop,
            name=f"master-os-agent-heartbeat-{run_id}",
            daemon=True,
        )
        thread.start()
        return stop_event, thread

    def dispatch_autonomous_job(
        self,
        packet: AgentJobPacket,
        agent_type: str = "codex",
        executor_func: Optional[Callable[[Path, AgentJobPacket], dict[str, Any]]] = None,
        *,
        resume_existing_workspace: bool = False,
    ) -> dict[str, Any]:
        """Execute an immediately dispatched authorized job."""
        if executor_func is None:
            raise RuntimeError(f"No real executor configured for agent type: {agent_type}")

        run_id = generate_id("RUN-")
        workspace = Path(packet.workspace_path).resolve()
        base_sha = self._get_head_sha(self.repo_root)
        if resume_existing_workspace:
            workspace = self._resume_workspace(packet)

        self._claim_task_run(run_id, packet, agent_type, base_sha)
        return self._execute_claimed_job(
            run_id,
            packet,
            agent_type,
            executor_func,
            resume_existing_workspace=resume_existing_workspace,
            workspace=workspace,
        )

    def execute_queued_job(
        self,
        run_id: str,
        packet: AgentJobPacket,
        *,
        agent_type: str = "codex",
        executor_func: Optional[Callable[[Path, AgentJobPacket], dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Claim and execute a durable queued run using its existing run identity."""
        if executor_func is None:
            raise RuntimeError(f"No real executor configured for agent type: {agent_type}")
        base_sha = self._get_head_sha(self.repo_root)
        self._claim_task_run(run_id, packet, agent_type, base_sha, require_queued=True)
        return self._execute_claimed_job(
            run_id,
            packet,
            agent_type,
            executor_func,
            resume_existing_workspace=False,
            workspace=Path(packet.workspace_path).resolve(),
        )

    def _execute_claimed_job(
        self,
        run_id: str,
        packet: AgentJobPacket,
        agent_type: str,
        executor_func: Callable[[Path, AgentJobPacket], dict[str, Any]],
        *,
        resume_existing_workspace: bool,
        workspace: Path,
    ) -> dict[str, Any]:
        source = self.events.register_source("agent_runner", f"{agent_type}_runner", f"runner-{agent_type}")
        heartbeat_stop, heartbeat_thread = self._start_heartbeat(run_id)

        exit_code = 1
        error_msg: Optional[str] = None
        produced_artifacts: list[str] = []
        findings: list[dict[str, Any]] = []

        try:
            if not resume_existing_workspace:
                workspace = self._prepare_workspace(packet)
            result = executor_func(workspace, packet)
            exit_code = int(result.get("exit_code", 1))
            produced_artifacts = list(result.get("artifacts", []))
            findings = list(result.get("findings", []))

            missing = [rel for rel in packet.expected_artifacts if not (workspace / rel).exists()]
            if missing:
                exit_code = 1
                error_msg = f"Missing expected artifacts: {', '.join(missing)}"

            run_status = "completed" if exit_code == 0 else "failed"
            task_status = "completed" if exit_code == 0 else "blocked"
        except Exception as exc:
            exit_code = 1
            error_msg = str(exc)
            run_status = "failed"
            task_status = "blocked"
        finally:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=max(1.0, self.heartbeat_interval_seconds * 2))

        registered_artifact_ids: list[str] = []
        for rel_art in produced_artifacts:
            art_file = workspace / rel_art
            if not art_file.exists():
                continue
            artifact = self.artifacts.register_file(
                file_path=art_file,
                artifact_type="experiment_metrics" if rel_art.endswith(".csv") else "document",
                git_sha=self._get_head_sha(workspace),
                created_by_agent_run=run_id,
            )
            registered_artifact_ids.append(artifact.id)

        for finding in findings:
            if not finding.get("statement"):
                continue
            self.commands.emit(
                event_type="finding.recorded",
                source_id=source.id,
                payload={
                    "id": generate_id("FIND-"),
                    "statement": finding["statement"],
                    "status": "candidate",
                    "confidence": finding.get("confidence", 0.5),
                },
            )

        self._finalize_run(
            run_id,
            packet.task_id,
            source.id,
            run_status=run_status,
            task_status=task_status,
            exit_code=exit_code,
            result_git_sha=self._get_head_sha(workspace),
            result_artifact_id=registered_artifact_ids[0] if registered_artifact_ids else None,
        )

        return {
            "run_id": run_id,
            "status": run_status,
            "task_status": task_status,
            "exit_code": exit_code,
            "error": error_msg,
            "artifacts": registered_artifact_ids,
        }

    def _finalize_run(
        self,
        run_id: str,
        task_id: str,
        source_id: str,
        *,
        run_status: str,
        task_status: str,
        exit_code: int,
        result_git_sha: Optional[str],
        result_artifact_id: Optional[str],
    ) -> None:
        """Commit run terminal state and task state in one transaction."""
        try:
            self.db.execute("BEGIN IMMEDIATE")
            complete_event = self.events.record_event(
                event_type="agent_run.completed",
                source_id=source_id,
                payload={
                    "id": run_id,
                    "status": run_status,
                    "exit_code": exit_code,
                    "result_git_sha": result_git_sha,
                    "result_artifact_id": result_artifact_id,
                    "failure_id": None,
                },
                dedup_key=f"agent-run-completed:{run_id}",
                commit=False,
            )
            apply_event(self.db, complete_event, commit=False)
            task_event = self.events.record_event(
                event_type="task.status_changed",
                source_id=source_id,
                payload={"id": task_id, "status": task_status},
                dedup_key=f"agent-run-task-final:{run_id}:{task_status}",
                commit=False,
            )
            apply_event(self.db, task_event, commit=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _get_head_sha(path: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None
