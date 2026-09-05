"""Assertion Resolver for Master OS."""
from __future__ import annotations

import json
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import Assertion, AuthorityLevel, generate_id, utc_now
from master_os.core.reducer import apply_event


class AssertionResolver:
    """Manage conflicting claims and resolve current-state fields by authority.

    Assertions are canonical semantic history, so writes always go through the
    event store. Direct SQL is reserved for reads/materialization performed by
    the reducer.
    """

    def __init__(self, db: MasterDatabase, events: Optional[EventStore] = None) -> None:
        self.db = db
        self.events = events or EventStore(db)

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
        """Record an event-backed assertion on a domain entity field."""
        as_id = generate_id("AS-")
        now = utc_now()
        source = self.events.register_source("assertion_resolver", "Assertion Resolver", "master-os-assertions")
        event = self.events.record_event(
            event_type="assertion.recorded",
            source_id=source.id,
            payload={
                "id": as_id,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "field": field,
                "value": value,
                "authority": int(authority),
                "confidence": confidence,
                "source_event_id": source_event_id,
                "valid_from": now,
                "supersedes_id": supersedes_id,
                "created_at": now,
            },
        )
        apply_event(self.db, event)

        resolved = self.db.fetchone("SELECT * FROM assertions WHERE id = ?", (as_id,))
        if not resolved:
            raise RuntimeError(f"Assertion event {event.id} did not materialize {as_id}")
        return self._row_to_assertion(resolved)

    def resolve_field(self, subject_type: str, subject_id: str, field: str) -> Optional[Assertion]:
        """Resolve the effective assertion.

        Precedence: authority, confidence, then recency.
        """
        row = self.db.fetchone(
            """SELECT * FROM assertions
               WHERE subject_type = ? AND subject_id = ? AND field = ? AND status = 'active'
               ORDER BY authority DESC, confidence DESC, valid_from DESC, rowid DESC LIMIT 1""",
            (subject_type, subject_id, field),
        )
        return self._row_to_assertion(row) if row else None

    def materialize_field(self, subject_type: str, subject_id: str, field: str) -> None:
        """Re-materialize a resolved field without creating new history.

        Normal writes already materialize inside ``apply_event``. This helper is
        retained for repair/administrative use.
        """
        resolved = self.resolve_field(subject_type, subject_id, field)
        if not resolved:
            return

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

        columns = [r["name"] for r in self.db.fetchall(f"PRAGMA table_info({table})")]
        if field not in columns:
            return

        value = resolved.value
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        sql = f"UPDATE {table} SET {field} = ?"
        params: list[Any] = [value]
        if "updated_at" in columns:
            sql += ", updated_at = ?"
            params.append(utc_now())
        sql += " WHERE id = ?"
        params.append(subject_id)
        self.db.execute(sql, tuple(params))
        self.db.commit()

    @staticmethod
    def _row_to_assertion(row: Any) -> Assertion:
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
