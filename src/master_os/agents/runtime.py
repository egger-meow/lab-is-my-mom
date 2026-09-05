"""Agent Runtime for authorized local execution in isolated workspaces."""
from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from master_os.agents.packet import AgentJobPacket
from master_os.core.artifacts import ArtifactRegistry
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
        self.artifacts = artifact_registry
        self.repo_root = repo_root.resolve()
        self.worktrees_dir = self.repo_root / ".master-os" / "worktrees"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        self.heartbeat_interval_seconds = 30.0

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
        # Empty is still a valid interrupted worktree, but it must already exist. We do
        # not recreate or reset anything here because the point of resume is evidence
        # preservation, not a disguised fresh retry.
        return path

    def _claim_task_run(
        self,
        run_id: str,
        packet: AgentJobPacket,
        agent_type: str,
        base_sha: Optional[str],
    ) -> None:
        """Atomically claim the task by materializing one active run.

        ``BEGIN IMMEDIATE`` serializes claim attempts across independent SQLite
        connections/processes. The canonical start event and materialized run row are
        committed together, so a rejected duplicate cannot leave a phantom event.
        """
        try:
            self.db.execute("BEGIN IMMEDIATE")
            active = self.db.fetchone(
                """SELECT id FROM agent_runs
                   WHERE task_id = ? AND status = 'running'
                   ORDER BY started_at DESC LIMIT 1""",
                (packet.task_id,),
            )
            if active:
                raise RuntimeError(
                    f"Task {packet.task_id} already has active agent run {active['id']}; lease is held"
                )

            start_event = self.events.record_event(
                event_type="agent_run.started",
                source_id=self.events.register_source(
                    "agent_runner", f"{agent_type}_runner", f"runner-{agent_type}"
                ).id,
                payload={
                    "id": run_id,
                    "agent_type": agent_type,
                    "job_type": "implementation",
                    "task_id": packet.task_id,
                    "workspace": str(Path(packet.workspace_path).resolve()),
                    "branch": packet.branch,
                    "base_git_sha": base_sha,
                    "packet_artifact_id": None,
                },
                commit=False,
            )
            apply_event(self.db, start_event, commit=False)
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

        # Publish immediately so recovery never sees a freshly started run with an
        # ambiguous NULL heartbeat.
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
        """Execute an authorized job and record only observed results.

        ``resume_existing_workspace`` is deliberately opt-in and intended only for
        an explicit interrupted-run recovery decision. Ordinary dispatch always
        demands a fresh isolated workspace.
        """
        if executor_func is None:
            raise RuntimeError(f"No real executor configured for agent type: {agent_type}")

        source = self.events.register_source("agent_runner", f"{agent_type}_runner", f"runner-{agent_type}")
        run_id = generate_id("RUN-")
        workspace = Path(packet.workspace_path).resolve()
        base_sha = self._get_head_sha(self.repo_root)

        # Validate explicit resume evidence before taking the task lease. This avoids
        # creating a phantom running row when the interrupted worktree vanished.
        if resume_existing_workspace:
            workspace = self._resume_workspace(packet)

        # Claim before touching a fresh worktree. A competing process sees the
        # committed running row and is rejected instead of creating a second run.
        self._claim_task_run(run_id, packet, agent_type, base_sha)
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
            # Task model has no 'failed' status. A failed/unfinished agent run leaves
            # work blocked for repair or user inspection rather than inventing a state.
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

        # Agent findings are always candidates. They are not silently validated.
        for finding in findings:
            if not finding.get("statement"):
                continue
            find_event = self.events.record_event(
                event_type="finding.recorded",
                source_id=source.id,
                payload={
                    "id": generate_id("FIND-"),
                    "statement": finding["statement"],
                    "status": "candidate",
                    "confidence": finding.get("confidence", 0.5),
                },
            )
            apply_event(self.db, find_event)

        complete_event = self.events.record_event(
            event_type="agent_run.completed",
            source_id=source.id,
            payload={
                "id": run_id,
                "status": run_status,
                "exit_code": exit_code,
                "result_git_sha": self._get_head_sha(workspace),
                "result_artifact_id": registered_artifact_ids[0] if registered_artifact_ids else None,
                "failure_id": None,
            },
        )
        apply_event(self.db, complete_event)

        task_event = self.events.record_event(
            event_type="task.status_changed",
            source_id=source.id,
            payload={"id": packet.task_id, "status": task_status},
        )
        apply_event(self.db, task_event)

        return {
            "run_id": run_id,
            "status": run_status,
            "task_status": task_status,
            "exit_code": exit_code,
            "error": error_msg,
            "artifacts": registered_artifact_ids,
        }

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
