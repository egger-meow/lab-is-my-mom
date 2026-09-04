"""Sandboxed Agent Runtime for autonomous local execution."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.models import generate_id, utc_now
from master_os.agents.packet import AgentJobPacket


class AgentRuntime:
    """Manages worktree sandboxes, agent dispatches, and acceptance verification."""

    def __init__(self, db: MasterDatabase, event_store: EventStore, artifact_registry: ArtifactRegistry, repo_root: Path) -> None:
        self.db = db
        self.events = event_store
        self.artifacts = artifact_registry
        self.repo_root = repo_root.resolve()
        self.worktrees_dir = self.repo_root / ".master-os" / "worktrees"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, branch_name: str) -> Path:
        """Create an isolated worktree directory for agent execution."""
        safe_branch = branch_name.replace("/", "-")
        worktree_path = self.worktrees_dir / safe_branch

        # If worktree already exists, remove it first
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

        try:
            # Try git worktree add if this is a git repo
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
        except Exception:
            # Fallback to local copy directory sandbox if git worktree fails (e.g. detached HEAD or branch exists)
            worktree_path.mkdir(parents=True, exist_ok=True)

        return worktree_path

    def cleanup_worktree(self, worktree_path: Path, branch_name: str) -> None:
        """Prune and clean up finished worktree."""
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

    def dispatch_autonomous_job(
        self,
        packet: AgentJobPacket,
        agent_type: str = "codex",
        executor_func: Optional[Callable[[Path, AgentJobPacket], dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Execute an authorized agent job in an isolated worktree with independent verification."""
        source = self.events.register_source("agent_runner", f"{agent_type}_runner", f"runner-{agent_type}")
        run_id = generate_id("RUN-")

        # 1. Emit agent_run.started event
        start_event = self.events.record_event(
            event_type="agent_run.started",
            source_id=source.id,
            payload={
                "id": run_id,
                "agent_type": agent_type,
                "job_type": "implementation",
                "task_id": packet.task_id,
                "workspace": packet.workspace_path,
                "branch": packet.branch,
                "base_git_sha": self._get_head_sha(),
                "packet_artifact_id": None,
            },
        )
        apply_event(self.db, start_event)

        worktree_path = Path(packet.workspace_path)
        worktree_path.mkdir(parents=True, exist_ok=True)

        exit_code = 0
        error_msg = None
        produced_artifacts: list[str] = []
        findings: list[dict[str, Any]] = []

        try:
            # 2. Execute the work in sandbox
            if executor_func:
                exec_result = executor_func(worktree_path, packet)
                exit_code = exec_result.get("exit_code", 0)
                produced_artifacts = exec_result.get("artifacts", [])
                findings = exec_result.get("findings", [])
            else:
                # Default mock executor for tests / dry-runs
                exit_code = 0

            # 3. Independent acceptance criteria verification: Agent says 'done' != Task completed
            criteria_passed = True
            for expected in packet.expected_artifacts:
                art_path = worktree_path / expected
                if not art_path.exists():
                    criteria_passed = False
                    error_msg = f"Missing expected artifact: {expected}"
                    exit_code = 1
                    break

            if criteria_passed and exit_code == 0:
                task_status = "completed"
                run_status = "completed"
            else:
                task_status = "failed"
                run_status = "failed"

        except Exception as e:
            exit_code = 1
            error_msg = str(e)
            run_status = "failed"
            task_status = "failed"

        # 4. Register artifacts
        registered_artifact_ids = []
        for rel_art in produced_artifacts:
            art_file = worktree_path / rel_art
            if art_file.exists():
                art = self.artifacts.register_file(
                    file_path=art_file,
                    artifact_type="experiment_metrics" if rel_art.endswith(".csv") else "document",
                    created_by_agent_run=run_id,
                )
                registered_artifact_ids.append(art.id)
                art_event = self.events.record_event(
                    event_type="artifact.created",
                    source_id=source.id,
                    payload={
                        "id": art.id,
                        "artifact_type": art.artifact_type,
                        "path": art.path,
                        "content_hash": art.content_hash,
                        "created_by_agent_run": run_id,
                    },
                )
                apply_event(self.db, art_event)

        # 5. Record findings if any
        for f in findings:
            find_id = generate_id("FIND-")
            find_event = self.events.record_event(
                event_type="finding.recorded",
                source_id=source.id,
                payload={
                    "id": find_id,
                    "statement": f["statement"],
                    "status": "candidate",
                    "confidence": f.get("confidence", 0.85),
                },
            )
            apply_event(self.db, find_event)

        # 6. Complete agent run & update task status
        complete_event = self.events.record_event(
            event_type="agent_run.completed",
            source_id=source.id,
            payload={
                "id": run_id,
                "status": run_status,
                "exit_code": exit_code,
                "result_git_sha": self._get_head_sha(),
                "result_artifact_id": registered_artifact_ids[0] if registered_artifact_ids else None,
                "failure_id": None if exit_code == 0 else "F-GENERIC",
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

    def _get_head_sha(self) -> Optional[str]:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout.strip()
        except Exception:
            return None
