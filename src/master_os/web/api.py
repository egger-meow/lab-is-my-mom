"""FastAPI backend application for Master OS Cockpit."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from master_os.agents.critic import MasterCritic
from master_os.agents.dispatcher import AgentDispatcher
from master_os.agents.packet import AgentJobPacket, WorkPacketBuilder
from master_os.agents.recovery_actions import AgentRecoveryActions
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.assertions import AssertionResolver
from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import AuthorityLevel, generate_id
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.lab.cadence import resolved_weekly_spec, routine_occurrence, validate_weekly_spec
from master_os.lab.protocol import SEMINAR_WEEKLY_SPEC
from master_os.scheduler.engine import SchedulerEngine
from master_os.supervisor.doctor import MasterDoctor

AgentExecutor = Callable[[Path, AgentJobPacket], dict[str, Any]]


class IngestTranscriptRequest(BaseModel):
    meeting_id: str
    transcript_text: str
    scheduled_at: Optional[str] = None
    kind: str = "advisor"
    title: Optional[str] = None


class AdvisorRoutineRequest(BaseModel):
    day_of_week: str
    start_time: str
    timezone: str = "Asia/Taipei"


class ScheduleMeetingRequest(BaseModel):
    meeting_id: Optional[str] = None
    title: Optional[str] = None
    kind: str = "advisor_adhoc"
    scheduled_at: str


class ResearchContextRequest(BaseModel):
    topic: str


class TaskStatusRequest(BaseModel):
    status: str


class DecideApprovalRequest(BaseModel):
    status: str
    note: Optional[str] = None


class RecoverAgentRunRequest(BaseModel):
    action: str
    note: Optional[str] = None


def _parse_json_field(value: Optional[str], fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _parse_aware_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="scheduled_at must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        raise HTTPException(status_code=400, detail="scheduled_at must include a timezone offset")
    return parsed


def create_app(
    db: MasterDatabase,
    repo_root: Path,
    agent_executors: Optional[dict[str, AgentExecutor]] = None,
) -> FastAPI:
    """Create the same-origin local Cockpit API and workspace UI."""
    app = FastAPI(title="Master OS Cockpit", version="0.5.1")

    executors = agent_executors or {}
    repo_root = repo_root.resolve()
    events = EventStore(db)
    commands = DomainCommandBus(db, events)
    assertions = AssertionResolver(db, events)
    artifacts = ArtifactRegistry(db, repo_root=repo_root, events=events)
    relations = RelationGraph(db, events=events)
    critic = MasterCritic(db)
    runtime = AgentRuntime(db, events, artifacts, repo_root=repo_root)
    packet_builder = WorkPacketBuilder(db)
    dispatcher = AgentDispatcher(db, repo_root, executors=executors)
    app.state.agent_dispatcher = dispatcher
    recovery_actions = AgentRecoveryActions(db, events, runtime, packet_builder, relations, repo_root)
    meeting_agent = MeetingAgent(db, events, artifacts, relations, repo_root=repo_root)
    planner = MasterPlanner(db)
    scheduler = SchedulerEngine(db, events, critic)
    doctor = MasterDoctor(db, repo_root=repo_root)

    def user_source():
        return events.register_source("user", "User Cockpit", "cockpit-ui", authority_class="user_explicit")

    def research_topic() -> Optional[str]:
        resolved = assertions.resolve_field("research_profile", "current", "topic")
        return str(resolved.value) if resolved and resolved.value else None

    def meeting_routines(now: Optional[datetime] = None) -> list[dict[str, Any]]:
        current = now or datetime.now(timezone.utc)
        advisor_spec = resolved_weekly_spec(db, "advisor")
        advisor_occurrence = routine_occurrence("advisor", "Weekly Advisor Meeting", advisor_spec, now=current) if advisor_spec else None
        seminar_spec = dict(SEMINAR_WEEKLY_SPEC)
        seminar_occurrence = routine_occurrence("lab_seminar", "Lab Seminar", seminar_spec, now=current)
        return [
            {
                "kind": "advisor",
                "title": "Weekly Advisor Meeting",
                "editable": True,
                "source": "user_explicit" if advisor_spec else "not_configured",
                "weekly_spec": advisor_spec,
                "next_occurrence": advisor_occurrence,
            },
            {
                "kind": "lab_seminar",
                "title": "Lab Seminar",
                "editable": False,
                "source": "NYCU NLP Lab 研究生需知",
                "weekly_spec": seminar_spec,
                "next_occurrence": seminar_occurrence,
                "note": "每週一 13:30–14:10，Google Meet；每週一位同學報論文。",
            },
        ]

    def upcoming_meetings(now: Optional[datetime] = None) -> list[dict[str, Any]]:
        routines = meeting_routines(now)
        items = [dict(r["next_occurrence"]) for r in routines if r.get("next_occurrence")]
        rows = db.fetchall("SELECT * FROM meetings WHERE status='scheduled' ORDER BY scheduled_at ASC LIMIT 50")
        for row in rows:
            item = dict(row)
            item["recurring"] = False
            item["explicit"] = True
            items.append(item)
        seen: set[str] = set()
        deduped = []
        for item in sorted(items, key=lambda value: value["scheduled_at"]):
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            deduped.append(item)
        return deduped

    def paper_snapshot(limit: int = 250) -> dict[str, Any]:
        paper_db = repo_root / ".research-os" / "research.db"
        if not paper_db.exists():
            return {"available": False, "count": 0, "papers": [], "database": str(paper_db)}
        conn = sqlite3.connect(str(paper_db))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """SELECT id,title,authors,year,venue,category,source_url,arxiv_id,doi,
                          fulltext_status,pdf_path,updated_at
                   FROM papers ORDER BY COALESCE(year,0) DESC,title LIMIT ?""",
                (limit,),
            ).fetchall()
            papers = [dict(row) for row in rows]
            total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
            fetched = conn.execute("SELECT COUNT(*) FROM papers WHERE fulltext_status='fetched'").fetchone()[0]
            processed = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            return {
                "available": True,
                "count": int(total),
                "fulltext_count": int(fetched),
                "processed_count": int(processed),
                "papers": papers,
                "database": str(paper_db),
            }
        except sqlite3.DatabaseError as exc:
            return {"available": False, "count": 0, "papers": [], "database": str(paper_db), "error": str(exc)}
        finally:
            conn.close()

    @app.get("/api/health")
    def health():
        return doctor.run_diagnostics()

    @app.get("/api/cockpit")
    def get_cockpit():
        plan = planner.get_plan()
        health_report = critic.evaluate_health()
        what_matters_now = {
            "focus_action": {
                "task_id": plan.focus_action.task_id,
                "title": plan.focus_action.title,
                "why": plan.focus_action.why,
                "estimated_minutes": plan.focus_action.estimated_minutes,
                "agentability": plan.focus_action.agentability,
                "suggested_agent": plan.focus_action.suggested_agent,
            },
            "critical_obligations": plan.critical_obligations,
            "research_velocity": health_report.research_velocity,
            "fake_progress_warning": health_report.fake_progress_warning,
            "warning_message": health_report.warning_message,
        }
        what_is_coming = {"upcoming_meetings": upcoming_meetings()[:5], "deadlines": plan.imminent_deadlines}
        findings_rows = db.fetchall("SELECT * FROM findings ORDER BY created_at DESC LIMIT 5")
        artifacts_rows = db.fetchall("SELECT * FROM artifacts ORDER BY created_at DESC LIMIT 5")
        what_changed = {
            "recent_findings": [dict(f) for f in findings_rows],
            "recent_artifacts": [dict(a) for a in artifacts_rows],
        }
        runs_rows = db.fetchall("SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT 8")
        what_are_agents_doing = {
            "recent_runs": [dict(r) for r in runs_rows],
            "inflight_runs": dispatcher.inflight(),
            "schedules": scheduler.list_schedules(),
        }
        approvals_rows = db.fetchall("SELECT * FROM approvals WHERE status = 'pending' ORDER BY requested_at DESC")
        parsed_approvals = []
        for row in approvals_rows:
            item = dict(row)
            item["action_payload"] = _parse_json_field(item.get("action_payload_json"), {})
            parsed_approvals.append(item)
        interrupted_runs = recovery_actions.list_interrupted()
        what_needs_me = {
            "pending_approvals": parsed_approvals,
            "approval_count": len(parsed_approvals),
            "interrupted_runs": interrupted_runs,
            "interrupted_run_count": len(interrupted_runs),
            "resource_burn_warnings": health_report.resource_burn_warnings,
        }
        return {
            "what_matters_now": what_matters_now,
            "what_is_coming": what_is_coming,
            "what_changed": what_changed,
            "what_are_agents_doing": what_are_agents_doing,
            "what_needs_me": what_needs_me,
        }

    @app.get("/api/onboarding")
    def onboarding():
        routines = meeting_routines()
        advisor = next(item for item in routines if item["kind"] == "advisor")
        transcript_count = db.fetchone("SELECT COUNT(*) AS n FROM meetings WHERE transcript_artifact_id IS NOT NULL")["n"]
        slack_count = db.fetchone("SELECT COUNT(*) AS n FROM sources WHERE type='slack_channel' AND enabled=1")["n"]
        topic = research_topic()
        steps = [
            {"id": "advisor_meeting", "label": "設定每週 Advisor Meeting 固定時間", "done": bool(advisor["weekly_spec"])},
            {"id": "research_topic", "label": "填入目前研究題目 / Hypothesis", "done": bool(topic)},
            {"id": "meeting_transcript", "label": "匯入最近一次 Meeting transcript / 筆記", "done": int(transcript_count) > 0},
            {"id": "slack", "label": "設定 Lab Slack scope（可稍後）", "done": int(slack_count) > 0, "optional": True},
        ]
        required = [step for step in steps if not step.get("optional")]
        return {
            "complete": all(step["done"] for step in required),
            "steps": steps,
            "research_topic": topic,
            "advisor_routine": advisor,
            "next_advisor_meeting": advisor.get("next_occurrence"),
        }

    @app.get("/api/tasks")
    def list_tasks():
        task_rows = db.fetchall(
            """SELECT t.*, o.title AS obligation_title, o.severity AS obligation_severity
               FROM tasks t LEFT JOIN obligations o ON o.id=t.obligation_id
               ORDER BY CASE t.status WHEN 'in_progress' THEN 0 WHEN 'todo' THEN 1 WHEN 'blocked' THEN 2 ELSE 3 END,
                        CASE t.priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                        t.due_at IS NULL,t.due_at,t.created_at DESC"""
        )
        tasks = []
        for row in task_rows:
            item = dict(row)
            item["acceptance_criteria"] = _parse_json_field(item.get("acceptance_criteria_json"), [])
            tasks.append(item)
        obligation_rows = db.fetchall(
            "SELECT * FROM obligations ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'active' THEN 1 ELSE 2 END, due_at IS NULL,due_at,created_at DESC"
        )
        obligations = []
        for row in obligation_rows:
            item = dict(row)
            item["satisfaction_rules"] = _parse_json_field(item.get("satisfaction_rules_json"), [])
            obligations.append(item)
        return {"tasks": tasks, "obligations": obligations}

    @app.post("/api/tasks/{task_id}/status")
    def change_task_status(task_id: str, req: TaskStatusRequest):
        allowed = {"todo", "in_progress", "blocked", "completed", "cancelled"}
        if req.status not in allowed:
            raise HTTPException(status_code=400, detail=f"status must be one of {sorted(allowed)}")
        if not db.fetchone("SELECT id FROM tasks WHERE id=?", (task_id,)):
            raise HTTPException(status_code=404, detail="task not found")
        source = user_source()
        event = commands.emit("task.status_changed", source.id, {"id": task_id, "status": req.status}, created_by="user_explicit")
        return {"task_id": task_id, "status": req.status, "event_id": event.id}

    @app.get("/api/meetings")
    def list_meetings():
        rows = db.fetchall("SELECT * FROM meetings ORDER BY scheduled_at DESC")
        explicit_upcoming = [dict(row) for row in rows if row["status"] == "scheduled"]
        history = [dict(row) for row in rows if row["status"] != "scheduled"]
        routines = meeting_routines()
        return {
            "routines": routines,
            "upcoming": upcoming_meetings(),
            "explicit_upcoming": sorted(explicit_upcoming, key=lambda item: item["scheduled_at"]),
            "history": history,
        }

    @app.post("/api/meetings/routines/advisor")
    def configure_advisor_routine(req: AdvisorRoutineRequest):
        try:
            spec = validate_weekly_spec({
                "day_of_week": req.day_of_week,
                "start_time": req.start_time,
                "timezone": req.timezone,
            })
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        assertion = assertions.assert_field(
            "meeting_routine",
            "advisor",
            "weekly_spec",
            spec,
            authority=AuthorityLevel.USER_EXPLICIT,
            confidence=1.0,
        )
        routine = next(item for item in meeting_routines() if item["kind"] == "advisor")
        return {"routine": routine, "assertion_id": assertion.id}

    def _schedule_explicit(req: ScheduleMeetingRequest) -> dict[str, Any]:
        parsed = _parse_aware_datetime(req.scheduled_at)
        meeting_id = (req.meeting_id or "").strip() or generate_id("M-")
        existing = db.fetchone("SELECT status FROM meetings WHERE id=?", (meeting_id,))
        if existing and existing["status"] == "completed":
            raise HTTPException(status_code=409, detail="completed meeting history cannot be rescheduled; create a new meeting")
        kind = req.kind.strip() or "advisor_adhoc"
        title = (req.title or "").strip() or ("Ad-hoc Advisor Meeting" if kind.startswith("advisor") else "Ad-hoc Meeting")
        source = user_source()
        event = commands.emit(
            "meeting.scheduled",
            source.id,
            {"id": meeting_id, "kind": kind, "title": title, "scheduled_at": parsed.isoformat(), "status": "scheduled"},
            created_by="user_explicit",
        )
        return {"meeting_id": meeting_id, "scheduled_at": parsed.isoformat(), "event_id": event.id}

    @app.post("/api/meetings/adhoc")
    def schedule_adhoc_meeting(req: ScheduleMeetingRequest):
        return _schedule_explicit(req)

    @app.post("/api/meetings/schedule")
    def schedule_meeting_legacy(req: ScheduleMeetingRequest):
        """Compatibility endpoint for old clients. New UI uses weekly routine + ad-hoc."""
        return _schedule_explicit(req)

    @app.post("/api/meetings/ingest")
    def ingest_transcript(req: IngestTranscriptRequest):
        existing = db.fetchone("SELECT id FROM meetings WHERE id=?", (req.meeting_id,))
        if not existing:
            if not req.scheduled_at:
                raise HTTPException(
                    status_code=409,
                    detail="Unknown meeting occurrence. Choose a recurring/ad-hoc meeting or provide its date/time; Master OS will not invent one.",
                )
            parsed = _parse_aware_datetime(req.scheduled_at)
            source = user_source()
            commands.emit(
                "meeting.scheduled",
                source.id,
                {
                    "id": req.meeting_id,
                    "kind": req.kind.strip() or "advisor",
                    "title": (req.title or "").strip() or "Advisor Meeting",
                    "scheduled_at": parsed.isoformat(),
                    "status": "scheduled",
                },
                created_by="user_explicit",
            )
        return meeting_agent.ingest_transcript(req.meeting_id, req.transcript_text)

    @app.post("/api/meetings/{meeting_id}/pack")
    def generate_meeting_pack(meeting_id: str):
        existing = db.fetchone("SELECT kind FROM meetings WHERE id=?", (meeting_id,))
        if meeting_id.startswith("M-SEM-") or (existing and existing["kind"] == "lab_seminar"):
            raise HTTPException(status_code=409, detail="Meeting Pack is for the weekly Advisor Meeting. Lab Seminar uses the separate Seminar Prep workflow.")
        return {"meeting_id": meeting_id, "meeting_pack": meeting_agent.generate_meeting_pack(meeting_id)}

    @app.get("/api/research")
    def research_workspace():
        experiments = [dict(row) for row in db.fetchall("SELECT * FROM experiments ORDER BY created_at DESC LIMIT 100")]
        findings = [dict(row) for row in db.fetchall("SELECT * FROM findings ORDER BY created_at DESC LIMIT 100")]
        decisions = [dict(row) for row in db.fetchall("SELECT * FROM decisions ORDER BY decided_at DESC LIMIT 100")]
        artifacts_rows = db.fetchall("SELECT * FROM artifacts WHERE canonical=1 ORDER BY created_at DESC LIMIT 100")
        artifact_items = []
        for row in artifacts_rows:
            item = dict(row)
            item["metadata"] = _parse_json_field(item.get("metadata_json"), {})
            artifact_items.append(item)
        return {
            "topic": research_topic(),
            "experiments": experiments,
            "findings": findings,
            "decisions": decisions,
            "artifacts": artifact_items,
        }

    @app.post("/api/research/context")
    def set_research_context(req: ResearchContextRequest):
        topic = req.topic.strip()
        if not topic:
            raise HTTPException(status_code=400, detail="topic cannot be empty")
        assertion = assertions.assert_field(
            "research_profile", "current", "topic", topic,
            authority=AuthorityLevel.USER_EXPLICIT, confidence=1.0,
        )
        return {"topic": topic, "assertion_id": assertion.id}

    @app.get("/api/papers")
    def list_papers():
        return paper_snapshot()

    @app.get("/api/agents")
    def agent_workspace():
        runs = [dict(row) for row in db.fetchall("SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT 200")]
        return {"runs": runs, "inflight": dispatcher.inflight(), "interrupted": recovery_actions.list_interrupted()}

    @app.get("/api/system")
    def system_workspace():
        sources = [dict(row) for row in db.fetchall("SELECT * FROM sources ORDER BY type,name")]
        schedules = scheduler.list_schedules()
        resources = []
        for row in db.fetchall("SELECT * FROM lab_resources ORDER BY resource_type,name"):
            item = dict(row)
            item["metadata"] = _parse_json_field(item.get("metadata_json"), {})
            item["active_containers"] = _parse_json_field(item.get("active_containers_json"), [])
            resources.append(item)
        health_rows = [dict(row) for row in db.fetchall("SELECT * FROM system_health ORDER BY subsystem")]
        return {
            "doctor": doctor.run_diagnostics(),
            "sources": sources,
            "schedules": schedules,
            "resources": resources,
            "health": health_rows,
            "research_os_database": str(repo_root / ".research-os" / "research.db"),
            "master_database": str(db.db_path),
        }

    @app.post("/api/approvals/{approval_id}/decide")
    def decide_approval(approval_id: str, req: DecideApprovalRequest):
        if req.status not in {"approved", "rejected"}:
            raise HTTPException(status_code=400, detail="status must be approved or rejected")
        approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
        if not approval:
            raise HTTPException(status_code=404, detail="approval not found")
        source = user_source()
        event = commands.emit(
            event_type="approval.decided",
            source_id=source.id,
            payload={"id": approval_id, "status": req.status, "decision_note": req.note or ""},
            created_by="user_explicit",
        )
        materialized_entity_id = None
        if req.status == "approved" and approval["action_type"] == "confirm_semantic_change":
            materialized_entity_id = meeting_agent.apply_semantic_approval(approval_id)
        return {
            "approval_id": approval_id,
            "status": req.status,
            "materialized_entity_id": materialized_entity_id,
            "event_id": event.id,
        }

    @app.get("/api/agent-runs/{run_id}/inspect")
    def inspect_agent_run(run_id: str):
        try:
            return recovery_actions.inspect(run_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/agent-runs/{run_id}/recover")
    def recover_agent_run(run_id: str, req: RecoverAgentRunRequest):
        if req.action not in {"resume", "retry_fresh", "abandon"}:
            raise HTTPException(status_code=400, detail="action must be resume, retry_fresh, or abandon")
        executor: Optional[AgentExecutor] = None
        if req.action in {"resume", "retry_fresh"}:
            run = db.fetchone("SELECT task_id, status FROM agent_runs WHERE id = ?", (run_id,))
            if not run:
                raise HTTPException(status_code=404, detail="agent run not found")
            task = db.fetchone("SELECT preferred_agent FROM tasks WHERE id = ?", (run["task_id"],))
            if not task:
                raise HTTPException(status_code=409, detail="interrupted run task no longer exists")
            agent_type = task["preferred_agent"] or "codex"
            executor = executors.get(agent_type)
            if executor is None:
                raise HTTPException(status_code=503, detail=f"No real {agent_type} executor is configured. Recovery cannot fabricate execution.")
        try:
            return recovery_actions.recover(run_id, req.action, executor=executor, note=req.note or "")
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/tasks/{task_id}/dispatch", status_code=202)
    def dispatch_task(task_id: str):
        task = db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        if task["agentability"] != "autonomous":
            raise HTTPException(status_code=409, detail="task is not authorized for autonomous execution")
        agent_type = task["preferred_agent"] or "codex"
        if agent_type not in executors:
            raise HTTPException(status_code=503, detail=f"No real {agent_type} executor is configured. Refusing to fabricate an agent result.")
        try:
            queued = dispatcher.enqueue_task(task_id)
            pump = dispatcher.pump_once()
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {**queued, "submitted": queued["run_id"] in pump["submitted"]}

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @app.get("/", response_class=HTMLResponse)
        def serve_ui():
            index_file = static_dir / "index.html"
            return index_file.read_text(encoding="utf-8") if index_file.exists() else "<h1>Master OS Cockpit Ready</h1>"

    return app
