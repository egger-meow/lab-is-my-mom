"""Production wiring for the long-lived Master OS supervisor."""
from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from master_os.agents.critic import MasterCritic
from master_os.agents.dispatcher import AgentDispatcher
from master_os.agents.executors import build_local_executors
from master_os.agents.recovery import AgentRecovery
from master_os.collectors.slack import SlackCollector
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.scheduler.engine import SchedulerEngine
from master_os.supervisor.backup import BackupManager
from master_os.supervisor.runtime import MasterSupervisor


SlackCollectorFactory = Callable[..., Any]
_ADVISOR_PREP_NAME = "Advisor Pre-Meeting Readiness & Pack"
_POST_MEETING_SLACK_NAME = "Advisor Post-Meeting Digest to Slack"


def parse_slack_conversations(value: str) -> list[tuple[str, str]]:
    """Parse ``conversation_id:scope`` entries from an explicit allow-list."""
    entries: list[tuple[str, str]] = []
    seen_channels: set[str] = set()
    seen_scopes: set[str] = set()
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if ":" not in raw:
            raise ValueError(
                "Each MASTER_OS_SLACK_CONVERSATIONS entry must be conversation_id:scope"
            )
        channel_id, scope = (part.strip() for part in raw.split(":", 1))
        if not channel_id or not scope:
            raise ValueError(
                "Each MASTER_OS_SLACK_CONVERSATIONS entry must include both conversation ID and scope"
            )
        if channel_id in seen_channels:
            raise ValueError(f"Duplicate Slack conversation ID: {channel_id}")
        if scope in seen_scopes:
            raise ValueError(f"Duplicate Slack scope: {scope}")
        seen_channels.add(channel_id)
        seen_scopes.add(scope)
        entries.append((channel_id, scope))
    return entries


def build_supervisor(
    db: MasterDatabase,
    repo_root: Path,
    *,
    env: Optional[Mapping[str, str]] = None,
    slack_collector_factory: SlackCollectorFactory = SlackCollector,
    agent_executors: Optional[dict[str, Any]] = None,
) -> MasterSupervisor:
    """Construct the production supervisor without performing external I/O."""
    config: Mapping[str, str] = os.environ if env is None else env
    token = str(config.get("SLACK_BOT_TOKEN", "")).strip()
    conversations_raw = str(config.get("MASTER_OS_SLACK_CONVERSATIONS", "")).strip()

    if conversations_raw and not token:
        raise ValueError(
            "MASTER_OS_SLACK_CONVERSATIONS is configured but SLACK_BOT_TOKEN is missing"
        )
    if token and not conversations_raw:
        raise ValueError(
            "SLACK_BOT_TOKEN is configured but MASTER_OS_SLACK_CONVERSATIONS is missing"
        )

    try:
        poll_seconds = float(str(config.get("MASTER_OS_SUPERVISOR_POLL_SECONDS", "60")).strip())
    except ValueError as exc:
        raise ValueError("MASTER_OS_SUPERVISOR_POLL_SECONDS must be numeric") from exc
    if poll_seconds <= 0:
        raise ValueError("MASTER_OS_SUPERVISOR_POLL_SECONDS must be positive")

    try:
        stale_seconds = float(str(config.get("MASTER_OS_AGENT_STALE_SECONDS", "180")).strip())
    except ValueError as exc:
        raise ValueError("MASTER_OS_AGENT_STALE_SECONDS must be numeric") from exc
    if stale_seconds <= 0:
        raise ValueError("MASTER_OS_AGENT_STALE_SECONDS must be positive")

    repo_root = repo_root.resolve()
    events = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root, events=events)
    relations = RelationGraph(db, events=events)
    meeting_agent = MeetingAgent(db, events, artifacts, relations, repo_root)
    planner = MasterPlanner(db)
    scheduler = SchedulerEngine(db, events, MasterCritic(db))
    recovery = AgentRecovery(db, events, stale_after_seconds=stale_seconds)
    dispatcher = AgentDispatcher(
        db,
        repo_root,
        executors=agent_executors if agent_executors is not None else build_local_executors(),
    )
    backups = BackupManager(db, repo_root)

    def handle_meeting_routine(item: dict[str, Any]) -> dict[str, Any]:
        name = item.get("name")
        context = item.get("context") or {}

        if name == _ADVISOR_PREP_NAME:
            meeting_id = str(context.get("meeting_id") or "").strip()
            if not meeting_id:
                raise RuntimeError("Advisor meeting-pack routine is missing meeting_id context")
            meeting_agent.generate_meeting_pack(meeting_id)
            return {
                "status": "ok",
                "meeting_id": meeting_id,
                "artifact_path": str(repo_root / "data" / "meeting_packs" / f"{meeting_id}_pack.md"),
            }

        if name == _POST_MEETING_SLACK_NAME:
            if context.get("event_type") != "meeting.completed":
                raise RuntimeError("Post-meeting Slack routine requires meeting.completed event context")
            event_payload = context.get("event_payload") or {}
            meeting_id = str(event_payload.get("id") or "").strip()
            if not meeting_id:
                raise RuntimeError("Post-meeting Slack routine is missing meeting_id in event payload")
            approval_id = meeting_agent.create_post_meeting_slack_approval_from_evidence(meeting_id)
            return {
                "status": "ok",
                "meeting_id": meeting_id,
                "approval_id": approval_id,
            }

        raise RuntimeError(
            f"No evidence-backed runtime handler is implemented for meeting routine {name!r}"
        )

    def handle_agent_dispatch_routine(item: dict[str, Any]) -> dict[str, Any]:
        policy = item.get("autonomy_policy") or {}
        if policy.get("dispatch_local") is not True:
            raise RuntimeError("Schedule does not authorize local autonomous dispatch")
        focus = planner.get_plan().focus_action
        if not focus.task_id:
            return {"status": "idle", "reason": "no focus task"}
        if focus.agentability != "autonomous":
            return {
                "status": "needs_user",
                "task_id": focus.task_id,
                "reason": "focus task is not autonomous",
            }
        queued = dispatcher.enqueue_task(focus.task_id)
        return {"status": "queued", **queued}

    def maintain_backup(current: datetime) -> dict[str, Any]:
        snapshots = sorted(
            backups.backup_dir.glob("master_snapshot_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if snapshots:
            age_seconds = max(0.0, current.timestamp() - snapshots[0].stat().st_mtime)
            if age_seconds < 24 * 60 * 60:
                return {
                    "status": "fresh",
                    "latest": str(snapshots[0]),
                    "age_seconds": int(age_seconds),
                }

        snapshot = backups.create_snapshot()
        integrity = backups.verify_integrity(snapshot)
        if not integrity["integrity_ok"] or integrity["foreign_key_violations"]:
            raise RuntimeError(f"Fresh backup failed integrity verification: {integrity}")

        snapshots = sorted(
            backups.backup_dir.glob("master_snapshot_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in snapshots[14:]:
            old.unlink(missing_ok=True)
        return {"status": "created", "snapshot": str(snapshot), "integrity": integrity}

    source_syncers: dict[str, Callable[[], dict[str, Any]]] = {}
    if token:
        collector = slack_collector_factory(db, events, token)
        for channel_id, scope in parse_slack_conversations(conversations_raw):
            source_syncers[f"slack:{scope}"] = _make_slack_syncer(collector, channel_id, scope)

    return MasterSupervisor(
        db,
        scheduler,
        routine_handlers={
            "meeting_agent": handle_meeting_routine,
            "agent_dispatcher": handle_agent_dispatch_routine,
        },
        source_syncers=source_syncers,
        recovery_handler=recovery.recover_stale_runs,
        agent_pump=dispatcher.pump_once,
        maintenance_handlers={"daily_backup": maintain_backup},
        poll_seconds=poll_seconds,
    )


def _make_slack_syncer(collector: Any, channel_id: str, scope: str) -> Callable[[], dict[str, Any]]:
    def sync() -> dict[str, Any]:
        result = collector.sync_channel(channel_id, scope_name=scope)
        if is_dataclass(result):
            return asdict(result)
        if isinstance(result, Mapping):
            return dict(result)
        raise TypeError("Slack collector sync result must be a dataclass or mapping")

    return sync
