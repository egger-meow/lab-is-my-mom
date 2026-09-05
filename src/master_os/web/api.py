"""FastAPI backend application for Master OS Cockpit."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from master_os.agents.critic import MasterCritic
from master_os.agents.packet import AgentJobPacket, WorkPacketBuilder
from master_os.agents.recovery_actions import AgentRecoveryActions
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.scheduler.engine import SchedulerEngine
from master_os.supervisor.doctor import MasterDoctor

AgentExecutor = Callable[[Path, AgentJobPacket], dict[str, Any]]


class IngestTranscriptRequest(BaseModel):
    meeting_id: str
    transcript_text: str


class DecideApprovalRequest(BaseModel):
    status: str
    note: Optional[str] = None


class RecoverAgentRunRequest(BaseModel):
    action: str
    note: Optional[str] = None


def create_app(
    db: MasterDatabase,
    repo_root: Path,
    agent_executors: Optional[dict[str, AgentExecutor]] = None,
) -> FastAPI:
    """Create the same-origin local cockpit API.

    Master OS intentionally does not enable permissive CORS. The UI is served by
    the same process, and remote access should use Tailscale Serve to proxy the
    loopback service rather than exposing a cross-origin mutation API.

    Production does not contain a demo executor. Real agent adapters are injected
    explicitly. Tests may inject deterministic executors without contaminating
    production behavior with fabricated metrics/findings.
    """
    app = FastAPI(title="Master OS Cockpit", version="0.3.0")

    executors = agent_executors or {}
    repo_root = repo_root.resolve()
    events = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root=repo_root, events=events)
    relations = RelationGraph(db, events=events)
    critic = MasterCritic(db)
    runtime = AgentRuntime(db, events, artifacts, repo_root=repo_root)
    packet_builder = WorkPacketBuilder(db)
    recovery_actions = AgentRecoveryActions(
        db,
        events,
        runtime,
        packet_builder,
        relations,
        repo_root,
    )
    meeting_agent = MeetingAgent(db, events, artifacts, relations, repo_root=repo_root)
    planner = MasterPlanner(db)
    scheduler = SchedulerEngine(db, events, critic)
    doctor = MasterDoctor(db, repo_root=repo_root)

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

        meetings_rows = db.fetchall(
            "SELECT * FROM meetings WHERE status = 'scheduled' ORDER BY scheduled_at ASC LIMIT 5"
        )
        what_is_coming = {
            "upcoming_meetings": [dict(m) for m in meetings_rows],
            "deadlines": plan.imminent_deadlines,
        }

        findings_rows = db.fetchall("SELECT * FROM findings ORDER BY created_at DESC LIMIT 5")
        artifacts_rows = db.fetchall("SELECT * FROM artifacts ORDER BY created_at DESC LIMIT 5")
        what_changed = {
            "recent_findings": [dict(f) for f in findings_rows],
            "recent_artifacts": [dict(a) for a in artifacts_rows],
        }

        runs_rows = db.fetchall("SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT 5")
        what_are_agents_doing = {
            "recent_runs": [dict(r) for r in runs_rows],
            "schedules": scheduler.list_schedules(),
        }

        approvals_rows = db.fetchall(
            "SELECT * FROM approvals WHERE status = 'pending' ORDER BY requested_at DESC"
        )
        parsed_approvals = []
        for row in approvals_rows:
            item = dict(row)
            item["action_payload"] = json.loads(item["action_payload_json"])
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

    @app.post("/api/meetings/ingest")
    def ingest_transcript(req: IngestTranscriptRequest):
        return meeting_agent.ingest_transcript(req.meeting_id, req.transcript_text)

    @app.post("/api/meetings/{meeting_id}/pack")
    def generate_meeting_pack(meeting_id: str):
        return {"meeting_id": meeting_id, "meeting_pack": meeting_agent.generate_meeting_pack(meeting_id)}

    @app.post("/api/approvals/{approval_id}/decide")
    def decide_approval(approval_id: str, req: DecideApprovalRequest):
        if req.status not in {"approved", "rejected"}:
            raise HTTPException(status_code=400, detail="status must be approved or rejected")
        approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
        if not approval:
            raise HTTPException(status_code=404, detail="approval not found")

        source = events.register_source("user", "User Cockpit", "cockpit-ui")
        event = events.record_event(
            event_type="approval.decided",
            source_id=source.id,
            payload={"id": approval_id, "status": req.status, "decision_note": req.note or ""},
            created_by="user_explicit",
        )
        apply_event(db, event)

        materialized_entity_id = None
        if req.status == "approved" and approval["action_type"] == "confirm_semantic_change":
            materialized_entity_id = meeting_agent.apply_semantic_approval(approval_id)

        return {
            "approval_id": approval_id,
            "status": req.status,
            "materialized_entity_id": materialized_entity_id,
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
                raise HTTPException(
                    status_code=503,
                    detail=f"No real {agent_type} executor is configured. Recovery cannot fabricate execution.",
                )

        try:
            return recovery_actions.recover(
                run_id,
                req.action,
                executor=executor,
                note=req.note or "",
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/tasks/{task_id}/dispatch")
    def dispatch_task(task_id: str):
        task = db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        if task["agentability"] != "autonomous":
            raise HTTPException(status_code=409, detail="task is not authorized for autonomous execution")

        agent_type = task["preferred_agent"] or "codex"
        executor = executors.get(agent_type)
        if executor is None:
            raise HTTPException(
                status_code=503,
                detail=f"No real {agent_type} executor is configured. Refusing to fabricate an agent result.",
            )

        ws_path = repo_root / ".master-os" / "worktrees" / f"auto-{task_id.lower()}"
        packet = packet_builder.build_packet(task_id, workspace_path=str(ws_path), repo_name=repo_root.name)
        return runtime.dispatch_autonomous_job(packet, agent_type=agent_type, executor_func=executor)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @app.get("/", response_class=HTMLResponse)
        def serve_ui():
            index_file = static_dir / "index.html"
            return index_file.read_text(encoding="utf-8") if index_file.exists() else "<h1>Master OS Cockpit Ready</h1>"

    return app
