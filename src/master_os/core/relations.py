"""Knowledge graph and relation management for Master OS."""
from __future__ import annotations

from typing import Any, Optional

from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import Relation, generate_id


class RelationGraph:
    """Manage provenance/research edges while preserving their history."""

    def __init__(self, db: MasterDatabase, events: Optional[EventStore] = None) -> None:
        self.db = db
        self.events = events or EventStore(db)
        self.commands = DomainCommandBus(db, self.events)

    def link(
        self,
        from_type: str,
        from_id: str,
        relation: str,
        to_type: str,
        to_id: str,
        source_event_id: Optional[str] = None,
    ) -> Relation:
        existing = self.db.fetchone(
            """SELECT * FROM relations
               WHERE from_type = ? AND from_id = ? AND relation = ? AND to_type = ? AND to_id = ? AND status = 'active'""",
            (from_type, from_id, relation, to_type, to_id),
        )
        if existing:
            return self._row_to_relation(existing)

        rid = generate_id("R-")
        source = self.events.register_source("relation_graph", "Relation Graph", "master-os-relations")
        event = self.commands.emit(
            event_type="relation.created",
            source_id=source.id,
            payload={
                "id": rid,
                "from_type": from_type,
                "from_id": from_id,
                "relation": relation,
                "to_type": to_type,
                "to_id": to_id,
                "source_event_id": source_event_id,
            },
        )
        row = self.db.fetchone("SELECT * FROM relations WHERE id = ?", (rid,))
        if not row:
            raise RuntimeError(f"Relation event {event.id} did not materialize {rid}")
        return self._row_to_relation(row)

    def invalidate(self, relation_id: str, source_event_id: Optional[str] = None) -> None:
        """Invalidate an edge through canonical history rather than deleting it."""
        current = self.db.fetchone("SELECT id, status FROM relations WHERE id = ?", (relation_id,))
        if not current or current["status"] == "invalidated":
            return
        source = self.events.register_source("relation_graph", "Relation Graph", "master-os-relations")
        self.commands.emit(
            event_type="relation.invalidated",
            source_id=source.id,
            payload={"id": relation_id, "source_event_id": source_event_id},
        )

    def get_out_relations(
        self,
        from_type: str,
        from_id: str,
        relation: Optional[str] = None,
        status: str = "active",
    ) -> list[Relation]:
        if relation:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE from_type = ? AND from_id = ? AND relation = ? AND status = ?",
                (from_type, from_id, relation, status),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE from_type = ? AND from_id = ? AND status = ?",
                (from_type, from_id, status),
            )
        return [self._row_to_relation(r) for r in rows]

    def get_in_relations(
        self,
        to_type: str,
        to_id: str,
        relation: Optional[str] = None,
        status: str = "active",
    ) -> list[Relation]:
        if relation:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE to_type = ? AND to_id = ? AND relation = ? AND status = ?",
                (to_type, to_id, relation, status),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE to_type = ? AND to_id = ? AND status = ?",
                (to_type, to_id, status),
            )
        return [self._row_to_relation(r) for r in rows]

    @staticmethod
    def _row_to_relation(row: Any) -> Relation:
        return Relation(
            id=row["id"],
            from_type=row["from_type"],
            from_id=row["from_id"],
            relation=row["relation"],
            to_type=row["to_type"],
            to_id=row["to_id"],
            status=row["status"],
            source_event_id=row["source_event_id"],
            created_at=row["created_at"],
        )
