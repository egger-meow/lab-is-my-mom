"""Agent Work Packet builder with Failure Memory injection."""
from __future__ import annotations

from dataclasses import dataclass, field
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
    """Assembles work packets by pulling task details, relations, and relevant failure memory."""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def build_packet(
        self,
        task_id: str,
        workspace_path: str,
        branch: Optional[str] = None,
        custom_permissions: Optional[dict[str, Any]] = None,
    ) -> AgentJobPacket:
        task = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        job_id = generate_id("JOB-")
        branch_name = branch or f"agent/{task_id.lower()}-{job_id[-4:]}"

        # Fetch obligation context if task is linked to one
        why = "General research task"
        if task["obligation_id"]:
            ob = self.db.fetchone("SELECT * FROM obligations WHERE id = ?", (task["obligation_id"],))
            if ob:
                why = f"Required to satisfy obligation [{ob['id']}]: '{ob['title']}' (Severity: {ob['severity']})"

        # Query failure memory to inject into packet
        failures = self.db.fetchall(
            "SELECT id, title, description, failure_type, root_cause, resolution, retry_condition FROM failures WHERE status = 'active' LIMIT 5"
        )
        known_failures = [
            {
                "id": f["id"],
                "title": f["title"],
                "failure_type": f["failure_type"],
                "root_cause": f["root_cause"],
                "resolution": f["resolution"],
                "retry_condition": f["retry_condition"],
            }
            for f in failures
        ]

        # Default sandboxed permissions (Repo autonomous, but NO external leaks)
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

        acceptance_criteria = []
        if task["acceptance_criteria_json"]:
            import json
            acceptance_criteria = json.loads(task["acceptance_criteria_json"])

        expected_artifacts = ["results/metrics.csv", "reports/summary.md"]

        return AgentJobPacket(
            job_id=job_id,
            task_id=task_id,
            objective=task["title"] + (f": {task['description']}" if task["description"] else ""),
            why=why,
            repo_name="routing-research",
            branch=branch_name,
            workspace_path=workspace_path,
            permissions=permissions,
            acceptance_criteria=acceptance_criteria,
            expected_artifacts=expected_artifacts,
            known_failures=known_failures,
        )
