"""SQLite persistence engine for Master OS."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    external_ref TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'default',
    enabled INTEGER NOT NULL DEFAULT 1,
    authority_class TEXT NOT NULL DEFAULT 'verified_source',
    created_at TEXT NOT NULL,
    last_synced_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(id),
    occurred_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    external_id TEXT,
    dedup_key TEXT UNIQUE,
    actor_ref TEXT,
    raw_ref TEXT,
    raw_hash TEXT,
    payload_json TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'system'
);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred_at ON events(occurred_at);

CREATE TABLE IF NOT EXISTS assertions (
    id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    field TEXT NOT NULL,
    value_json TEXT NOT NULL,
    authority INTEGER NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    source_event_id TEXT REFERENCES events(id),
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    supersedes_id TEXT REFERENCES assertions(id),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assertions_subject ON assertions(subject_type, subject_id, field);
CREATE INDEX IF NOT EXISTS idx_assertions_status ON assertions(status);

CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    actual_started_at TEXT,
    actual_ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled',
    transcript_artifact_id TEXT,
    meeting_pack_artifact_id TEXT,
    previous_meeting_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled ON meetings(scheduled_at);

CREATE TABLE IF NOT EXISTS obligations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    severity TEXT NOT NULL DEFAULT 'normal',
    due_at TEXT,
    starts_at TEXT,
    owner TEXT NOT NULL DEFAULT 'student',
    meeting_id TEXT REFERENCES meetings(id),
    source_event_id TEXT REFERENCES events(id),
    satisfaction_rules_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obligations_due ON obligations(due_at);
CREATE INDEX IF NOT EXISTS idx_obligations_status ON obligations(status);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    due_at TEXT,
    obligation_id TEXT REFERENCES obligations(id) ON DELETE SET NULL,
    agentability TEXT NOT NULL DEFAULT 'autonomous',
    preferred_agent TEXT NOT NULL DEFAULT 'codex',
    acceptance_criteria_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_obligation ON tasks(obligation_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    job_type TEXT NOT NULL,
    task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    started_at TEXT,
    finished_at TEXT,
    heartbeat_at TEXT,
    workspace TEXT,
    branch TEXT,
    base_git_sha TEXT,
    result_git_sha TEXT,
    packet_artifact_id TEXT,
    result_artifact_id TEXT,
    exit_code INTEGER,
    failure_id TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_task ON agent_runs(task_id);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    research_repo TEXT NOT NULL DEFAULT 'routing-research',
    status TEXT NOT NULL DEFAULT 'planned',
    git_sha TEXT,
    dataset_ref TEXT,
    config_artifact_id TEXT,
    compute_backend TEXT NOT NULL DEFAULT 'local',
    remote_job_ref TEXT,
    started_at TEXT,
    finished_at TEXT,
    validity_status TEXT NOT NULL DEFAULT 'under_review',
    created_by_task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    canonical INTEGER NOT NULL DEFAULT 1,
    git_sha TEXT,
    created_by_agent_run TEXT REFERENCES agent_runs(id) ON DELETE SET NULL,
    created_by_experiment TEXT REFERENCES experiments(id) ON DELETE SET NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_artifacts_hash ON artifacts(content_hash);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate',
    confidence REAL NOT NULL DEFAULT 0.8,
    experiment_id TEXT REFERENCES experiments(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    validated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);

CREATE TABLE IF NOT EXISTS failures (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    failure_type TEXT NOT NULL,
    root_cause TEXT,
    resolution TEXT,
    retry_condition TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_failures_status ON failures(status);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    decided_at TEXT NOT NULL,
    superseded_by TEXT REFERENCES decisions(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL,
    action_payload_json TEXT NOT NULL DEFAULT '{}',
    reason TEXT NOT NULL DEFAULT '',
    risk_level TEXT NOT NULL DEFAULT 'medium',
    estimated_cost REAL,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TEXT NOT NULL,
    decided_at TEXT,
    decision_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    trigger_spec_json TEXT NOT NULL DEFAULT '{}',
    agent_role TEXT NOT NULL DEFAULT 'general',
    prompt_template TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    catch_up_policy TEXT NOT NULL DEFAULT 'run_once',
    autonomy_policy_json TEXT NOT NULL DEFAULT '{}',
    last_run_at TEXT,
    next_run_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relations (
    id TEXT PRIMARY KEY,
    from_type TEXT NOT NULL,
    from_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    to_type TEXT NOT NULL,
    to_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    source_event_id TEXT REFERENCES events(id),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_type, from_id);
CREATE INDEX IF NOT EXISTS idx_relations_to ON relations(to_type, to_id);
CREATE INDEX IF NOT EXISTS idx_relations_status ON relations(status);

CREATE TABLE IF NOT EXISTS lab_resources (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ok',
    quota_limit REAL NOT NULL DEFAULT 0.0,
    quota_used REAL NOT NULL DEFAULT 0.0,
    cost_estimate REAL NOT NULL DEFAULT 0.0,
    burn_rate_warning INTEGER NOT NULL DEFAULT 0,
    active_containers_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_health (
    subsystem TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'ok',
    last_heartbeat TEXT NOT NULL,
    message TEXT,
    details_json TEXT NOT NULL DEFAULT '{}'
);
"""


class MasterDatabase:
    """Manages SQLite database connections, schema lifecycle, and queries."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path.resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), autocommit=True)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(SCHEMA_SQL)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        return cursor.execute(sql, parameters)

    def executemany(self, sql: str, seq_of_parameters: list[tuple[Any, ...]]) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        return cursor.executemany(sql, seq_of_parameters)

    def fetchall(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        cursor = self.execute(sql, parameters)
        return cursor.fetchall()

    def fetchone(self, sql: str, parameters: tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        cursor = self.execute(sql, parameters)
        return cursor.fetchone()

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()

    def close(self) -> None:
        self.conn.close()

    def clear_materialized_state(self) -> None:
        """Clear materialized tables for deterministic state rebuild, keeping events and sources."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        for table in [
            "assertions", "meetings", "obligations", "tasks", "agent_runs",
            "experiments", "artifacts", "findings", "failures", "decisions",
            "approvals", "schedules", "relations", "lab_resources"
        ]:
            cursor.execute(f"DELETE FROM {table}")
        cursor.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()
