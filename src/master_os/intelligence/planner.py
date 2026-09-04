"""Master Planner for Master OS: Critical path, obligation prioritization, and next-action selection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from master_os.core.database import MasterDatabase


@dataclass
class FocusAction:
    task_id: Optional[str]
    title: str
    why: str
    estimated_minutes: int
    agentability: str
    suggested_agent: str
    linked_obligation_id: Optional[str]


@dataclass
class PlannerState:
    focus_action: FocusAction
    critical_obligations: list[dict[str, Any]]
    imminent_deadlines: list[dict[str, Any]]
    active_tasks_count: int
    blocked_tasks_count: int


class MasterPlanner:
    """Answers the ultimate question: 'What is the single most important thing to do right now, and why?'"""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def get_plan(self) -> PlannerState:
        # 1. Fetch critical obligations
        obs = self.db.fetchall(
            """SELECT * FROM obligations 
               WHERE status IN ('pending', 'in_progress')
               ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END, due_at ASC"""
        )

        critical_obs = [
            {
                "id": o["id"],
                "title": o["title"],
                "severity": o["severity"],
                "status": o["status"],
                "due_at": o["due_at"],
            }
            for o in obs
        ]

        # 2. Find executable tasks (status in 'todo', 'in_progress')
        tasks = self.db.fetchall(
            """SELECT t.*, o.severity as ob_severity, o.title as ob_title 
               FROM tasks t
               LEFT JOIN obligations o ON t.obligation_id = o.id
               WHERE t.status IN ('todo', 'in_progress')
               ORDER BY 
                 CASE t.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
                 CASE COALESCE(o.severity, 'normal') WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END,
                 t.created_at ASC"""
        )

        active_count = len(tasks)
        blocked_row = self.db.fetchone("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'blocked'")
        blocked_count = blocked_row["cnt"] if blocked_row else 0

        # 3. Determine single next focus action
        if tasks:
            top_task = tasks[0]
            why_text = f"Priority: {top_task['priority'].upper()}"
            if top_task["obligation_id"]:
                why_text += f" | 關聯核心 Obligation [{top_task['obligation_id']}]: {top_task['ob_title']}"

            # Estimated time: shorter for review/decision, longer for implementation
            est_time = 8 if top_task["agentability"] == "autonomous" else 45

            focus = FocusAction(
                task_id=top_task["id"],
                title=top_task["title"],
                why=why_text,
                estimated_minutes=est_time,
                agentability=top_task["agentability"],
                suggested_agent=top_task["preferred_agent"],
                linked_obligation_id=top_task["obligation_id"],
            )
        else:
            focus = FocusAction(
                task_id=None,
                title="所有待辦任務已清空，審視最新文獻或規劃下一輪 Hypothesis",
                why="目前無積壓任務，建議啟動文獻探勘或閱讀新進論文",
                estimated_minutes=15,
                agentability="interactive",
                suggested_agent="research_agent",
                linked_obligation_id=None,
            )

        # 4. Upcoming meetings / deadlines
        meetings = self.db.fetchall(
            "SELECT id, title, scheduled_at, kind FROM meetings WHERE status = 'scheduled' ORDER BY scheduled_at ASC LIMIT 3"
        )
        deadlines = [
            {"id": m["id"], "title": m["title"], "date": m["scheduled_at"], "type": "meeting"}
            for m in meetings
        ]

        return PlannerState(
            focus_action=focus,
            critical_obligations=critical_obs,
            imminent_deadlines=deadlines,
            active_tasks_count=active_count,
            blocked_tasks_count=blocked_count,
        )
