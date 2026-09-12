"""Evidence-backed daily planning and user check-ins, without promoting research truth."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from master_os.core.assertions import AssertionResolver
from master_os.core.commands import DomainCommandBus
from master_os.core.events import EventStore
from master_os.core.models import AuthorityLevel
from master_os.lab.cadence import resolved_weekly_spec, routine_occurrence

PLAN_FILE = "research-plan.json"
DEFAULT_PREFERENCES = {
    "enabled": False, "timezone": "Asia/Taipei", "daily_time": "09:00",
    "heavy_days": ["sat", "sun", "mon"], "heavy_minutes": 240, "light_minutes": 60,
}
KINDS = {"research", "reading", "experiment_design", "local_analysis", "synthesis", "human_review"}


def task_work(db, task_id: str) -> dict[str, Any]:
    item = AssertionResolver(db).resolve_field("task", task_id, "research_work")
    return item.value if item and isinstance(item.value, dict) else {}


class DailyResearchPlanner:
    def __init__(self, db, repo_root: Path):
        self.db, self.root = db, Path(repo_root).resolve()
        self.events = EventStore(db)
        self.commands = DomainCommandBus(db, self.events)
        self.assertions = AssertionResolver(db, self.events)

    def preferences(self) -> dict[str, Any]:
        item = self.assertions.resolve_field("research_profile", "current", "work_preferences")
        return {**DEFAULT_PREFERENCES, **(item.value if item else {})}

    def configure(self, value: dict[str, Any]) -> dict[str, Any]:
        p = {**self.preferences(), **value}
        ZoneInfo(p["timezone"])
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", p["daily_time"]):
            raise ValueError("daily_time must be HH:MM")
        if not isinstance(p["enabled"], bool) or not set(p["heavy_days"]) <= {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}:
            raise ValueError("invalid planning preferences")
        if any(type(p[k]) is not int or not 15 <= p[k] <= 720 for k in ("heavy_minutes", "light_minutes")):
            raise ValueError("daily capacity must be 15..720 minutes")
        self.assertions.assert_field("research_profile", "current", "work_preferences", p, authority=AuthorityLevel.USER_EXPLICIT)
        return p

    def next_meeting(self, now: datetime) -> dict[str, Any] | None:
        items = []
        spec = resolved_weekly_spec(self.db, "advisor")
        if spec:
            items.append(routine_occurrence("advisor", "Weekly Advisor Meeting", spec, now=now))
        for row in self.db.fetchall("SELECT * FROM meetings WHERE kind IN ('advisor','advisor_adhoc') AND status='scheduled'"):
            if datetime.fromisoformat(row["scheduled_at"]) > now:
                items.append(dict(row))
        return min(items, key=lambda x: datetime.fromisoformat(x["scheduled_at"])) if items else None

    def check_in(self, text: str, completed_task_ids: list[str] | None = None) -> dict[str, Any]:
        text = text.strip()
        if not text or len(text) > 12000:
            raise ValueError("progress text must contain 1..12000 characters")
        ids = list(dict.fromkeys(completed_task_ids or []))
        for task_id in ids:
            if not self.db.fetchone("SELECT id FROM tasks WHERE id=?", (task_id,)):
                raise ValueError(f"unknown task: {task_id}")
        source = self.events.register_source("user", "Daily progress", "daily-progress", authority_class="user_explicit")
        event = self.commands.emit("research.progress_reported", source.id, {"text": text, "completed_task_ids": ids}, raw_content=text, created_by="user_explicit")
        for task_id in ids:
            self.commands.emit("task.status_changed", source.id, {"id": task_id, "status": "completed"}, dedup_key=f"checkin:{event.id}:{task_id}", created_by="user_explicit")
        return {"event_id": event.id, "text": text}

    def context(self, now: datetime) -> dict[str, Any]:
        documents = []
        # Include ignored/uncommitted evidence in the frozen packet, not just paths
        # that won't exist in an isolated Git checkout. Never read credentials.
        paths = list((self.root / "data" / "documents").glob("*.txt")) + list((self.root / "data" / "transcripts").glob("*.txt"))
        for path in sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)[:12]:
            if path.resolve().is_relative_to(self.root):
                text = path.read_text(encoding="utf-8", errors="replace")
                documents.append({"ref": path.relative_to(self.root).as_posix(), "text": text[:14000], "truncated": len(text) > 14000})
        rows = self.db.fetchall("SELECT * FROM tasks WHERE status IN ('todo','in_progress','blocked') ORDER BY created_at DESC LIMIT 60")
        tasks = [{**dict(r), "work": task_work(self.db, r["id"])} for r in rows if r["preferred_agent"] != "research_planner"]
        progress = [json.loads(r["payload_json"]) for r in self.db.fetchall("SELECT payload_json FROM events WHERE event_type='research.progress_reported' ORDER BY rowid DESC LIMIT 12")]
        return {"today": now.astimezone(ZoneInfo(self.preferences()["timezone"])).date().isoformat(),
                "preferences": self.preferences(), "next_meeting": self.next_meeting(now),
                "documents": documents, "progress": progress, "active_tasks": tasks,
                "finished_tasks": [dict(r) for r in self.db.fetchall("SELECT id,title,status FROM tasks WHERE status IN ('completed','cancelled') ORDER BY updated_at DESC LIMIT 30")],
                "recent_findings": [dict(r) for r in self.db.fetchall("SELECT * FROM findings ORDER BY created_at DESC LIMIT 8")]}

    def request_plan(self, now: datetime | None = None, *, reason: str = "daily", dispatcher=None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("planner clock must be timezone-aware")
        active = self.db.fetchone("SELECT ar.id,ar.task_id,ar.status FROM agent_runs ar JOIN tasks t ON t.id=ar.task_id WHERE t.preferred_agent='research_planner' AND ar.status IN ('queued','running','recovering') LIMIT 1")
        if active:
            return {"status": active["status"], "run_id": active["id"], "task_id": active["task_id"]}
        context = self.context(now)
        if not context["next_meeting"]:
            return {"status": "needs_meeting", "reason": "請先設定下一次個人 meeting"}
        latest = self.db.fetchone("SELECT id FROM events WHERE event_type IN ('research.progress_reported','research.document_imported','meeting.transcript.imported') ORDER BY rowid DESC LIMIT 1")
        settings = hashlib.sha256(json.dumps([context['preferences'], context['next_meeting']], sort_keys=True).encode()).hexdigest()[:12]
        key = f"{context['today']}:{latest['id'] if latest else 'initial'}:{settings}"
        task_id = "T-PLAN-" + hashlib.sha256(key.encode()).hexdigest()[:16]
        if self.db.fetchone("SELECT id FROM tasks WHERE id=?", (task_id,)):
            run = self.db.fetchone("SELECT id,status FROM agent_runs WHERE task_id=? ORDER BY created_at DESC LIMIT 1", (task_id,))
            if not run and dispatcher:
                return dispatcher.enqueue_task(task_id)
            if run and run["status"] in ("failed", "interrupted") and reason == "manual" and dispatcher:
                source = self.events.register_source("research_planner", "Daily research planner", "daily-research-planner")
                self.commands.emit("task.status_changed", source.id, {"id": task_id, "status": "todo"})
                return dispatcher.enqueue_task(task_id)
            return {"status": run["status"] if run else "todo", "task_id": task_id, "run_id": run["id"] if run else None}
        source = self.events.register_source("research_planner", "Daily research planner", "daily-research-planner")
        self.commands.emit("task.created", source.id, {"id": task_id, "title": "整理研究進度並安排 meeting 前工作", "description": "根據最新會議、參考資料、進度回報與現有任務，拆出具體調查、研究、實驗設計與報告工作。", "priority": "high", "agentability": "autonomous", "preferred_agent": "research_planner", "acceptance_criteria": ["輸出有來源、問題、方法、交付物、依賴及日期的 research-plan.json；不得宣布選題或捏造進度"]}, dedup_key=f"daily-plan-task:{task_id}")
        work = {"kind": "planning", "scheduled_for": context["today"], "estimated_minutes": 10, "expected_artifacts": [PLAN_FILE], "context": context}
        self.assertions.assert_field("task", task_id, "research_work", work)
        return dispatcher.enqueue_task(task_id) if dispatcher else {"status": "todo", "task_id": task_id}

    def tick(self, now: datetime, dispatcher) -> dict[str, Any]:
        p = self.preferences()
        if not p["enabled"]:
            return {"status": "disabled"}
        local = now.astimezone(ZoneInfo(p["timezone"]))
        if local.strftime("%H:%M") < p["daily_time"]:
            return {"status": "waiting", "next_time": p["daily_time"]}
        return self.request_plan(now, dispatcher=dispatcher)

    def apply_plan(self, plan: dict[str, Any], *, context: dict[str, Any], run_id: str) -> list[str]:
        """Validate a bounded proposal completely before materializing any tasks.

        No model-proposed status, permission, obligation or decision is accepted.
        Existing tasks are only rescheduled, never silently completed/cancelled.
        """
        if not isinstance(plan, dict) or not isinstance(plan.get("summary"), str) or not isinstance(plan.get("tasks"), list) or not 1 <= len(plan["tasks"]) <= 12:
            raise ValueError("plan requires summary and 1..12 tasks")
        today = date.fromisoformat(context["today"])
        deadline = datetime.fromisoformat(context["next_meeting"]["scheduled_at"])
        zone = ZoneInfo(context["preferences"]["timezone"])
        final_day = deadline.astimezone(zone).date()
        allowed_refs = {d["ref"] for d in context["documents"]}
        allowed_ids = {t["id"] for t in context["active_tasks"]}
        keys, prepared, totals = set(), [], {}
        for item in plan["tasks"]:
            if not isinstance(item, dict):
                raise ValueError("task must be an object")
            for field in ("key", "title", "question", "method", "deliverable"):
                if not isinstance(item.get(field), str) or not item[field].strip() or len(item[field]) > 4000:
                    raise ValueError(f"task requires bounded {field}")
            if not re.fullmatch(r"[a-z0-9_-]{1,60}", item["key"]) or item["key"] in keys:
                raise ValueError("task keys must be unique stable slugs")
            keys.add(item["key"])
            if item.get("kind") not in KINDS:
                raise ValueError("unsupported research task kind")
            day = date.fromisoformat(item["scheduled_for"])
            if not today <= day <= final_day:
                raise ValueError("task date outside meeting preparation window")
            minutes = item.get("estimated_minutes")
            if type(minutes) is not int or not 5 <= minutes <= 240:
                raise ValueError("task estimate must be 5..240 minutes")
            totals[day] = totals.get(day, 0) + minutes
            refs = item.get("evidence_refs", [])
            if not isinstance(refs, list) or not refs or any(not isinstance(r, str) or r not in allowed_refs for r in refs):
                raise ValueError("tasks need evidence references from the supplied context")
            existing_id = item.get("existing_task_id")
            if existing_id and existing_id not in allowed_ids:
                raise ValueError("existing_task_id must refer to an active task in the supplied context")
            deps = item.get("depends_on", [])
            if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
                raise ValueError("depends_on must be task keys")
            task_id = existing_id or "T-RES-" + hashlib.sha256(f"{context['next_meeting']['id']}:{item['key']}".encode()).hexdigest()[:16]
            prepared.append((item, task_id))
        ids = {item["key"]: tid for item, tid in prepared}
        if len(set(ids.values())) != len(ids):
            raise ValueError("each existing task may only appear once")
        for old in context["active_tasks"]:
            work = old.get("work", {})
            if old["id"] in ids.values() or work.get("kind") not in KINDS:
                continue
            old_day = work.get("scheduled_for")
            if old_day and date.fromisoformat(old_day) <= final_day:
                day = max(today, date.fromisoformat(old_day))
                totals[day] = totals.get(day, 0) + work.get("estimated_minutes", 0)
        days = {item["key"]: item["scheduled_for"] for item, _ in prepared}
        for item, _ in prepared:
            if any(d not in ids or days[d] > item["scheduled_for"] for d in item.get("depends_on", [])):
                raise ValueError("dependency missing or scheduled after its consumer")
        graph = {item["key"]: item.get("depends_on", []) for item, _ in prepared}
        def visit(key, stack):
            if key in stack:
                raise ValueError("cyclic task dependencies")
            for dep in graph[key]:
                visit(dep, stack | {key})
        for key in graph:
            visit(key, set())
        p = context["preferences"]
        for day, minutes in totals.items():
            weekday = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[day.weekday()]
            if minutes > p["heavy_minutes" if weekday in p["heavy_days"] else "light_minutes"]:
                raise ValueError("plan exceeds daily study capacity")
        source = self.events.register_source("research_planner", "Daily research planner", "daily-research-planner")
        materialized = []
        for item, tid in prepared:
            existing = self.db.fetchone("SELECT status FROM tasks WHERE id=?", (tid,))
            if existing and existing["status"] in ("completed", "cancelled"):
                continue
            spec = {"id": tid, "title": item["title"], "description": f"研究問題：{item['question']}\n方法：{item['method']}\n交付物：{item['deliverable']}", "priority": "high", "due_at": deadline.isoformat(), "agentability": "interactive" if item["kind"] in ("human_review", "reading", "local_analysis") else "autonomous", "preferred_agent": "codex", "acceptance_criteria": [item["deliverable"], "標明來源、已驗證結果與尚待確認的假設；不得把文獻結果當自己的實驗"]}
            work = {k: item[k] for k in ("key", "title", "question", "method", "deliverable", "kind", "scheduled_for", "estimated_minutes", "evidence_refs")}
            work.update({"meeting_id": context["next_meeting"]["id"], "dependencies": [ids[d] for d in item.get("depends_on", [])], "plan_run_id": run_id, "proposal": True, "expected_artifacts": ["research-output.md"]})
            materialized.append({"task": spec, "work": work})
        self.commands.emit("research.plan.applied", source.id, {"run_id": run_id, "summary": plan["summary"], "task_ids": list(ids.values()), "tasks": materialized, "meeting_id": context["next_meeting"]["id"]}, dedup_key=f"research-plan-applied:{run_id}")
        return list(ids.values())

    def status(self) -> dict[str, Any]:
        rows = self.db.fetchall("SELECT event_type,payload_json,occurred_at FROM events WHERE event_type IN ('research.progress_reported','research.plan.applied','research.plan.failed') ORDER BY rowid DESC LIMIT 15")
        run = self.db.fetchone("SELECT ar.id,ar.status,ar.started_at,ar.finished_at FROM agent_runs ar JOIN tasks t ON t.id=ar.task_id WHERE t.preferred_agent='research_planner' ORDER BY ar.created_at DESC LIMIT 1")
        return {"preferences": self.preferences(), "latest_run": dict(run) if run else None, "history": [{"type": r["event_type"], "at": r["occurred_at"], **json.loads(r["payload_json"])} for r in rows]}
