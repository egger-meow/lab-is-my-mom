"""Assertion Resolver for Master OS."""
from __future__ import annotations

import json
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.models import Assertion, AuthorityLevel, generate_id, utc_now


class AssertionResolver:
    """Manages conflicting claims and resolves current state fields based on authority."""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def assert_field(
        self,
        subject_type: str,
        subject_id: str,
        field: str,
        value: Any,
        authority: int = AuthorityLevel.AGENT_INTERPRETATION,
        confidence: float = 1.0,
        source_event_id: Optional[str] = None,
        supersedes_id: Optional[str] = None,
    ) -> Assertion:
        """Record an assertion on a domain entity field."""
        as_id = generate_id("AS-")
        now = utc_now()
        val_json = json.dumps(value, ensure_ascii=False)

        # If explicit supersedes_id provided, mark old assertion as superseded
        if supersedes_id:
            self.db.execute(
                "UPDATE assertions SET status = 'superseded', valid_until = ? WHERE id = ?",
                (now, supersedes_id)
            )

        self.db.execute(
            """INSERT INTO assertions (id, subject_type, subject_id, field, value_json, authority,
                                      confidence, source_event_id, valid_from, status, supersedes_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
            (as_id, subject_type, subject_id, field, val_json, authority, confidence, source_event_id, now, supersedes_id, now)
        )
        self.db.commit()

        # Materialize onto target table
        self.materialize_field(subject_type, subject_id, field)

        return Assertion(
            id=as_id,
            subject_type=subject_type,
            subject_id=subject_id,
            field=field,
            value=value,
            authority=authority,
            confidence=confidence,
            source_event_id=source_event_id,
            valid_from=now,
            status="active",
            supersedes_id=supersedes_id,
            created_at=now,
        )

    def resolve_field(self, subject_type: str, subject_id: str, field: str) -> Optional[Assertion]:
        """Resolve the effective assertion for a subject field.
        
        Precedence:
        1. Authority (Highest wins: user_explicit > verified_source > confirmed > agent > heuristic)
        2. Confidence (Highest wins)
        3. Recency (Latest valid_from wins)
        """
        rows = self.db.fetchall(
            """SELECT * FROM assertions 
               WHERE subject_type = ? AND subject_id = ? AND field = ? AND status = 'active'
               ORDER BY authority DESC, confidence DESC, valid_from DESC LIMIT 1""",
            (subject_type, subject_id, field)
        )
        if not rows:
            return None

        row = rows[0]
        return Assertion(
            id=row["id"],
            subject_type=row["subject_type"],
            subject_id=row["subject_id"],
            field=row["field"],
            value=json.loads(row["value_json"]),
            authority=row["authority"],
            confidence=row["confidence"],
            source_event_id=row["source_event_id"],
            valid_from=row["valid_from"],
            valid_until=row["valid_until"],
            status=row["status"],
            supersedes_id=row["supersedes_id"],
            created_at=row["created_at"],
        )

    def materialize_field(self, subject_type: str, subject_id: str, field: str) -> None:
        """Update the materialized column in the current-state relational table."""
        resolved = self.resolve_field(subject_type, subject_id, field)
        if not resolved:
            return

        # Map subject_type to table name (pluralized)
        table_map = {
            "meeting": "meetings",
            "task": "tasks",
            "obligation": "obligations",
            "experiment": "experiments",
            "decision": "decisions",
            "finding": "findings",
        }
        table = table_map.get(subject_type)
        if not table:
            return

        # Check if table has column
        cursor = self.db.execute(f"PRAGMA table_info({table})")
        columns = [r["name"] for r in cursor.fetchall()]
        if field not in columns:
            return

        val = resolved.value
        if isinstance(val, (dict, list)):
            val = json.dumps(val, ensure_ascii=False)

        now = utc_now()
        update_clause = f"UPDATE {table} SET {field} = ?"
        params: list[Any] = [val]
        if "updated_at" in columns:
            update_clause += ", updated_at = ?"
            params.append(now)
        update_clause += " WHERE id = ?"
        params.append(subject_id)

        self.db.execute(update_clause, tuple(params))
        self.db.commit()
