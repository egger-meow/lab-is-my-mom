"""Agent Work Packet builder with Failure Memory injection."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.models import generate_id, utc_now


@dataclass
class AgentJobPacket:
    """Bounded, self-contained work packet dispatched to Codex/Antigravity."""

    job_id: str
    task_id: str
    objective: str
    why: str
    repo_name: str
    branch: str
    workspace_path: str
    permissions: dict[str, Any]
    acceptance_criteria: list[str]
    expected_artifacts: list[str]
    known_failures: list[dict[str, Any]] = field(default_factory=list)
    context_notes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)


class WorkPacketBuilder:
    """Assemble work packets from confirmed task state and relevant memory."""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def build_packet(
        self,
        task_id: str,
        workspace_path: str,
        branch: Optional[str] = None,
        custom_permissions: Optional[dict[str, Any]] = None,
        repo_name: Optional[str] = None,
        expected_artifacts: Optional[list[str]] = None,
    ) -> AgentJobPacket:
        task = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        job_id = generate_id("JOB-")
        branch_name = branch or f"agent/{task_id.lower()}-{job_id[-4:]}"

        why = "General research task"
        if task["obligation_id"]:
            ob = self.db.fetchone("SELECT * FROM obligations WHERE id = ?", (task["obligation_id"],))
            if ob:
                why = f"Required to satisfy obligation [{ob['id']}]: '{ob['title']}' (Severity: {ob['severity']})"

        # V1 relevance filtering is conservative: only active failures are injected.
        # Never fabricate failure memory; future graph-based filtering can narrow this further.
        failures = self.db.fetchall(
            """SELECT id, title, description, failure_type, root_cause, resolution, retry_condition
               FROM failures WHERE status = 'active' ORDER BY created_at DESC LIMIT 5"""
        )
        known_failures = [
            {
                "id": f["id"],
                "title": f["title"],
                "description": f["description"],
                "failure_type": f["failure_type"],
                "root_cause": f["root_cause"],
                "resolution": f["resolution"],
                "retry_condition": f["retry_condition"],
            }
            for f in failures
        ]

        permissions = {
            "filesystem": "worktree_only",
            "network": False,
            "slack": "none",
            "email": "none",
            "merge_main": False,
            "costly_compute": False,
        }
        if custom_permissions:
            permissions.update(custom_permissions)

        acceptance_criteria: list[str] = []
        if task["acceptance_criteria_json"]:
            acceptance_criteria = json.loads(task["acceptance_criteria_json"])

        # Repo identity and expected outputs are task/dispatcher context. They are never
        # guessed as routing-research or a canned metrics/report pair.
        inferred_repo = Path(workspace_path).resolve().parent.name or "unknown-repo"

        return AgentJobPacket(
            job_id=job_id,
            task_id=task_id,
            objective=task["title"] + (f": {task['description']}" if task["description"] else ""),
            why=why,
            repo_name=repo_name or inferred_repo,
            branch=branch_name,
            workspace_path=workspace_path,
            permissions=permissions,
            acceptance_criteria=acceptance_criteria,
            expected_artifacts=list(expected_artifacts or []),
            known_failures=known_failures,
        )
