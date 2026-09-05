"""Agent Runtime for authorized local execution in isolated workspaces."""
from __future__ import annotations

import subprocess
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

    def _prepare_workspace(self, packet: AgentJobPacket) -> Path:
        """Prepare the requested workspace without silently degrading isolation."""
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

    def dispatch_autonomous_job(
        self,
        packet: AgentJobPacket,
        agent_type: str = "codex",
        executor_func: Optional[Callable[[Path, AgentJobPacket], dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Execute an authorized job and record only observed results."""
        if executor_func is None:
            raise RuntimeError(f"No real executor configured for agent type: {agent_type}")

        source = self.events.register_source("agent_runner", f"{agent_type}_runner", f"runner-{agent_type}")
        run_id = generate_id("RUN-")
        workspace = Path(packet.workspace_path).resolve()
        base_sha = self._get_head_sha(self.repo_root)

        # Claim before touching the worktree. A competing process sees the committed
        # running row and is rejected instead of creating a second workspace/run.
        self._claim_task_run(run_id, packet, agent_type, base_sha)

        exit_code = 1
        error_msg: Optional[str] = None
        produced_artifacts: list[str] = []
        findings: list[dict[str, Any]] = []

        try:
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
