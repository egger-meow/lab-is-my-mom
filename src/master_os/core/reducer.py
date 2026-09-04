"""Deterministic state transition reducer for Master OS."""
from __future__ import annotations

import json
from typing import Any

from master_os.core.database import MasterDatabase
from master_os.core.models import Event, utc_now


def apply_event(db: MasterDatabase, event: Event) -> None:
    """Apply a single canonical domain event to update materialized state."""
    etype = event.event_type
    p = event.payload
    now = event.occurred_at or utc_now()

    if etype == "meeting.scheduled":
        mid = p["id"]
        db.execute(
            """INSERT INTO meetings (id, kind, title, scheduled_at, status, previous_meeting_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
               kind=excluded.kind, title=excluded.title, scheduled_at=excluded.scheduled_at,
               status=excluded.status, updated_at=excluded.updated_at""",
            (mid, p.get("kind", "advisor"), p["title"], p["scheduled_at"], p.get("status", "scheduled"),
             p.get("previous_meeting_id"), now, now)
        )

    elif etype == "meeting.completed":
        mid = p["id"]
        db.execute(
            """UPDATE meetings SET status = 'completed', actual_ended_at = ?,
               transcript_artifact_id = COALESCE(?, transcript_artifact_id),
               meeting_pack_artifact_id = COALESCE(?, meeting_pack_artifact_id),
               updated_at = ? WHERE id = ?""",
            (now, p.get("transcript_artifact_id"), p.get("meeting_pack_artifact_id"), now, mid)
        )

    elif etype == "obligation.created":
        oid = p["id"]
        rules_json = json.dumps(p.get("satisfaction_rules", []), ensure_ascii=False)
        db.execute(
            """INSERT INTO obligations (id, title, description, status, severity, due_at, starts_at, owner,
                                       meeting_id, source_event_id, satisfaction_rules_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
               title=excluded.title, description=excluded.description, status=excluded.status,
               severity=excluded.severity, due_at=excluded.due_at, updated_at=excluded.updated_at""",
            (oid, p["title"], p.get("description", ""), p.get("status", "pending"), p.get("severity", "normal"),
             p.get("due_at"), p.get("starts_at"), p.get("owner", "student"), p.get("meeting_id"),
             event.id, rules_json, now, now)
        )

    elif etype == "obligation.satisfied":
        oid = p["id"]
        db.execute("UPDATE obligations SET status = 'satisfied', updated_at = ? WHERE id = ?", (now, oid))

    elif etype == "task.created":
        tid = p["id"]
        crit_json = json.dumps(p.get("acceptance_criteria", []), ensure_ascii=False)
        db.execute(
            """INSERT INTO tasks (id, title, description, status, priority, due_at, obligation_id,
                                 agentability, preferred_agent, acceptance_criteria_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
               title=excluded.title, description=excluded.description, status=excluded.status,
               priority=excluded.priority, due_at=excluded.due_at, updated_at=excluded.updated_at""",
            (tid, p["title"], p.get("description", ""), p.get("status", "todo"), p.get("priority", "medium"),
             p.get("due_at"), p.get("obligation_id"), p.get("agentability", "autonomous"),
             p.get("preferred_agent", "codex"), crit_json, now, now)
        )

    elif etype == "task.status_changed":
        tid = p["id"]
        db.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (p["status"], now, tid))

    elif etype == "agent_run.started":
        rid = p["id"]
        db.execute(
            """INSERT INTO agent_runs (id, agent_type, job_type, task_id, status, started_at,
                                      workspace, branch, base_git_sha, packet_artifact_id, created_at)
               VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status='running', started_at=excluded.started_at""",
            (rid, p["agent_type"], p["job_type"], p.get("task_id"), now, p.get("workspace"),
             p.get("branch"), p.get("base_git_sha"), p.get("packet_artifact_id"), now)
        )

    elif etype == "agent_run.completed":
        rid = p["id"]
        db.execute(
            """UPDATE agent_runs SET status = ?, finished_at = ?, result_git_sha = ?,
               result_artifact_id = ?, exit_code = ?, failure_id = ? WHERE id = ?""",
            (p.get("status", "completed"), now, p.get("result_git_sha"), p.get("result_artifact_id"),
             p.get("exit_code", 0), p.get("failure_id"), rid)
        )

    elif etype == "experiment.created":
        eid = p["id"]
        db.execute(
            """INSERT INTO experiments (id, title, research_repo, status, git_sha, dataset_ref,
                                       config_artifact_id, compute_backend, remote_job_ref, started_at,
                                       validity_status, created_by_task_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, validity_status=excluded.validity_status""",
            (eid, p["title"], p.get("research_repo", "routing-research"), p.get("status", "planned"),
             p.get("git_sha"), p.get("dataset_ref"), p.get("config_artifact_id"), p.get("compute_backend", "local"),
             p.get("remote_job_ref"), p.get("started_at"), p.get("validity_status", "under_review"),
             p.get("created_by_task_id"), now)
        )

    elif etype == "experiment.finished":
        eid = p["id"]
        db.execute(
            """UPDATE experiments SET status = ?, finished_at = ?, validity_status = ? WHERE id = ?""",
            (p.get("status", "completed"), now, p.get("validity_status", "valid"), eid)
        )

    elif etype == "artifact.created":
        aid = p["id"]
        meta_json = json.dumps(p.get("metadata", {}), ensure_ascii=False)
        db.execute(
            """INSERT INTO artifacts (id, artifact_type, path, content_hash, canonical, git_sha,
                                     created_by_agent_run, created_by_experiment, metadata_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET canonical=excluded.canonical""",
            (aid, p["artifact_type"], p["path"], p["content_hash"], int(p.get("canonical", True)),
             p.get("git_sha"), p.get("created_by_agent_run"), p.get("created_by_experiment"), meta_json, now)
        )

    elif etype == "finding.recorded":
        fid = p["id"]
        db.execute(
            """INSERT INTO findings (id, statement, status, confidence, experiment_id, created_at, validated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, confidence=excluded.confidence""",
            (fid, p["statement"], p.get("status", "candidate"), p.get("confidence", 0.8),
             p.get("experiment_id"), now, p.get("validated_at"))
        )

    elif etype == "finding.validated":
        fid = p["id"]
        db.execute("UPDATE findings SET status = 'validated', validated_at = ? WHERE id = ?", (now, fid))

    elif etype == "failure.recorded":
        fid = p["id"]
        db.execute(
            """INSERT INTO failures (id, title, description, failure_type, root_cause, resolution,
                                    retry_condition, status, created_at, resolved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, resolution=excluded.resolution""",
            (fid, p["title"], p["description"], p["failure_type"], p.get("root_cause"),
             p.get("resolution"), p.get("retry_condition"), p.get("status", "active"), now, p.get("resolved_at"))
        )

    elif etype == "decision.recorded":
        did = p["id"]
        db.execute(
            """INSERT INTO decisions (id, statement, rationale, status, decided_at, superseded_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, rationale=excluded.rationale""",
            (did, p["statement"], p.get("rationale", ""), p.get("status", "active"), p.get("decided_at", now),
             p.get("superseded_by"), now)
        )

    elif etype == "approval.requested":
        apid = p["id"]
        payload_json = json.dumps(p.get("action_payload", {}), ensure_ascii=False)
        db.execute(
            """INSERT INTO approvals (id, action_type, action_payload_json, reason, risk_level,
                                     estimated_cost, status, requested_at)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
               ON CONFLICT(id) DO UPDATE SET status='pending'""",
            (apid, p["action_type"], payload_json, p.get("reason", ""), p.get("risk_level", "medium"),
             p.get("estimated_cost"), now)
        )

    elif etype == "approval.decided":
        apid = p["id"]
        db.execute(
            """UPDATE approvals SET status = ?, decided_at = ?, decision_note = ? WHERE id = ?""",
            (p["status"], now, p.get("decision_note"), apid)
        )

    elif etype == "relation.created":
        rid = p["id"]
        db.execute(
            """INSERT INTO relations (id, from_type, from_id, relation, to_type, to_id, status, source_event_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
               ON CONFLICT(id) DO UPDATE SET status='active'""",
            (rid, p["from_type"], p["from_id"], p["relation"], p["to_type"], p["to_id"], event.id, now)
        )

    elif etype == "relation.invalidated":
        rid = p["id"]
        db.execute("UPDATE relations SET status = 'invalidated' WHERE id = ?", (rid,))

    elif etype == "assertion.recorded":
        as_id = p["id"]
        val_json = json.dumps(p["value"], ensure_ascii=False)
        db.execute(
            """INSERT INTO assertions (id, subject_type, subject_id, field, value_json, authority,
                                      confidence, source_event_id, valid_from, status, supersedes_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
               ON CONFLICT(id) DO UPDATE SET status='active', value_json=excluded.value_json""",
            (as_id, p["subject_type"], p["subject_id"], p["field"], val_json, p.get("authority", 200),
             p.get("confidence", 1.0), event.id, now, p.get("supersedes_id"), now)
        )

    elif etype == "lab_resource.updated":
        rid = p["id"]
        containers_json = json.dumps(p.get("active_containers", []), ensure_ascii=False)
        meta_json = json.dumps(p.get("metadata", {}), ensure_ascii=False)
        db.execute(
            """INSERT INTO lab_resources (id, resource_type, name, status, quota_limit, quota_used,
                                         cost_estimate, burn_rate_warning, active_containers_json, metadata_json, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
               status=excluded.status, quota_limit=excluded.quota_limit, quota_used=excluded.quota_used,
               cost_estimate=excluded.cost_estimate, burn_rate_warning=excluded.burn_rate_warning,
               active_containers_json=excluded.active_containers_json, metadata_json=excluded.metadata_json,
               updated_at=excluded.updated_at""",
            (rid, p["resource_type"], p["name"], p.get("status", "ok"), p.get("quota_limit", 0.0),
             p.get("quota_used", 0.0), p.get("cost_estimate", 0.0), int(p.get("burn_rate_warning", False)),
             containers_json, meta_json, now)
        )

    db.commit()


def rebuild_state(db: MasterDatabase) -> int:
    """Deterministic state rebuild from canonical event history.
    
    Returns count of replayed events.
    """
    db.clear_materialized_state()
    events_cursor = db.execute("SELECT * FROM events ORDER BY occurred_at ASC, rowid ASC")
    rows = events_cursor.fetchall()

    replayed = 0
    for row in rows:
        event = Event(
            id=row["id"],
            event_type=row["event_type"],
            source_id=row["source_id"],
            occurred_at=row["occurred_at"],
            ingested_at=row["ingested_at"],
            external_id=row["external_id"],
            dedup_key=row["dedup_key"],
            actor_ref=row["actor_ref"],
            raw_ref=row["raw_ref"],
            raw_hash=row["raw_hash"],
            payload=json.loads(row["payload_json"]),
            created_by=row["created_by"],
        )
        apply_event(db, event)
        replayed += 1

    return replayed
