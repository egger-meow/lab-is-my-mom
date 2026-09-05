"""Domain models and semantic identifiers for Master OS."""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Optional


def utc_now() -> str:
    """Return ISO-8601 formatted UTC timestamp with seconds resolution."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AuthorityLevel(IntEnum):
    """Authority hierarchy for semantic assertions and resolution."""
    HEURISTIC_INFERENCE = 100
    AGENT_INTERPRETATION = 200
    CONFIRMED_SEMANTIC = 300
    VERIFIED_SOURCE = 400
    USER_EXPLICIT = 500


def generate_id(prefix: str) -> str:
    """Generate human-readable prefixed identifiers with collision-resistant entropy.

    Examples: EV-20260905-a3f1b2c3d4e5, T-20260905-88c2d1e4f6a7.

    The date remains useful to humans/agents while the 48-bit random suffix is
    large enough for a long-lived local event store without relying on opaque UUIDs.
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    token = secrets.token_hex(6)  # 12 hex chars = 48 bits
    return f"{prefix}{date_part}-{token}"


@dataclass
class Source:
    id: str
    type: str  # slack_channel, manual_upload, git_repo, experiment_runner, email, web
    name: str
    external_ref: str
    scope: str = "default"
    enabled: bool = True
    authority_class: str = "verified_source"
    created_at: str = field(default_factory=utc_now)
    last_synced_at: Optional[str] = None


@dataclass
class Event:
    id: str
    event_type: str
    source_id: str
    occurred_at: str
    ingested_at: str = field(default_factory=utc_now)
    external_id: Optional[str] = None
    dedup_key: Optional[str] = None
    actor_ref: Optional[str] = None
    raw_ref: Optional[str] = None
    raw_hash: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_by: str = "system"


@dataclass
class Assertion:
    id: str
    subject_type: str  # meeting, task, obligation, etc.
    subject_id: str
    field: str
    value: Any
    authority: int = AuthorityLevel.AGENT_INTERPRETATION
    confidence: float = 1.0
    source_event_id: Optional[str] = None
    valid_from: str = field(default_factory=utc_now)
    valid_until: Optional[str] = None
    status: str = "active"  # active, superseded, retracted
    supersedes_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class Meeting:
    id: str
    kind: str  # advisor, lab_seminar, course, other
    title: str
    scheduled_at: str
    actual_started_at: Optional[str] = None
    actual_ended_at: Optional[str] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    transcript_artifact_id: Optional[str] = None
    meeting_pack_artifact_id: Optional[str] = None
    previous_meeting_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Obligation:
    id: str
    title: str
    description: str = ""
    status: str = "pending"  # pending, in_progress, satisfied, breached, waived
    severity: str = "normal"  # critical, high, normal, low
    due_at: Optional[str] = None
    starts_at: Optional[str] = None
    owner: str = "student"
    meeting_id: Optional[str] = None
    source_event_id: Optional[str] = None
    satisfaction_rules: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: str = "todo"  # todo, in_progress, completed, blocked, cancelled
    priority: str = "medium"  # critical, high, medium, low
    due_at: Optional[str] = None
    obligation_id: Optional[str] = None
    agentability: str = "autonomous"  # autonomous, human_only, interactive
    preferred_agent: str = "codex"  # codex, antigravity, research_agent, human
    acceptance_criteria: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class AgentRun:
    id: str
    agent_type: str  # codex, antigravity, meeting_agent, critic
    job_type: str  # implementation, review, extraction, test
    task_id: Optional[str] = None
    status: str = "queued"  # queued, running, completed, failed, cancelled
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    heartbeat_at: Optional[str] = None
    workspace: Optional[str] = None
    branch: Optional[str] = None
    base_git_sha: Optional[str] = None
    result_git_sha: Optional[str] = None
    packet_artifact_id: Optional[str] = None
    result_artifact_id: Optional[str] = None
    exit_code: Optional[int] = None
    failure_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class Experiment:
    id: str
    title: str
    research_repo: str = ""
    status: str = "planned"  # planned, running, completed, failed, cancelled
    git_sha: Optional[str] = None
    dataset_ref: Optional[str] = None
    config_artifact_id: Optional[str] = None
    compute_backend: str = "local"  # local, nchc, lab_workstation, h100
    remote_job_ref: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    validity_status: str = "under_review"  # valid, partially_valid, invalid, under_review
    created_by_task_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class Artifact:
    id: str
    artifact_type: str  # transcript, meeting_pack, plot, metrics, code, etc.
    path: str
    content_hash: str
    canonical: bool = True
    git_sha: Optional[str] = None
    created_by_agent_run: Optional[str] = None
    created_by_experiment: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)


@dataclass
class Finding:
    id: str
    statement: str
    status: str = "candidate"  # candidate, validated, rejected, superseded
    confidence: float = 0.8
    experiment_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
    validated_at: Optional[str] = None


@dataclass
class Failure:
    id: str
    title: str
    description: str
    failure_type: str  # calibration_error, oom, timeout, bad_assumption, syntax
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    retry_condition: Optional[str] = None
    status: str = "active"  # active, resolved, mitigated
    created_at: str = field(default_factory=utc_now)
    resolved_at: Optional[str] = None


@dataclass
class Decision:
    id: str
    statement: str
    rationale: str = ""
    status: str = "active"  # active, superseded, abandoned
    decided_at: str = field(default_factory=utc_now)
    superseded_by: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class Approval:
    id: str
    action_type: str  # send_slack, send_email, start_nchc, merge_main, paid_api
    action_payload: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    risk_level: str = "medium"  # low, medium, high, critical
    estimated_cost: Optional[float] = None
    status: str = "pending"  # pending, approved, rejected, expired
    requested_at: str = field(default_factory=utc_now)
    decided_at: Optional[str] = None
    decision_note: Optional[str] = None


@dataclass
class Schedule:
    id: str
    name: str
    trigger_type: str  # time_cron, interval, event, condition
    trigger_spec: dict[str, Any] = field(default_factory=dict)
    agent_role: str = "general"
    prompt_template: str = ""
    enabled: bool = True
    catch_up_policy: str = "run_once"  # run_once, skip, run_all
    autonomy_policy: dict[str, Any] = field(default_factory=dict)
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Relation:
    id: str
    from_type: str
    from_id: str
    relation: str  # created, requires, depends_on, supported_by, motivated, invalidates
    to_type: str
    to_id: str
    status: str = "active"  # active, invalidated, superseded
    source_event_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class LabResource:
    id: str
    resource_type: str  # nchc, openai, lab_gpu, h100
    name: str
    status: str = "ok"  # ok, warning, critical_burn, exhausted
    quota_limit: float = 0.0
    quota_used: float = 0.0
    cost_estimate: float = 0.0
    burn_rate_warning: bool = False
    active_containers_json: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now)
