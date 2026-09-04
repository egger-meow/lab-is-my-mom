"""Knowledge graph and relation management for Master OS."""
from __future__ import annotations

from typing import Optional
from master_os.core.database import MasterDatabase
from master_os.core.models import Relation, generate_id, utc_now


class RelationGraph:
    """Manages generalized property relations and provenance links."""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def link(
        self,
        from_type: str,
        from_id: str,
        relation: str,
        to_type: str,
        to_id: str,
        source_event_id: Optional[str] = None,
    ) -> Relation:
        """Create an active relation edge."""
        existing = self.db.fetchone(
            """SELECT * FROM relations 
               WHERE from_type = ? AND from_id = ? AND relation = ? AND to_type = ? AND to_id = ? AND status = 'active'""",
            (from_type, from_id, relation, to_type, to_id)
        )
        if existing:
            return self._row_to_relation(existing)

        rid = generate_id("R-")
        now = utc_now()
        self.db.execute(
            """INSERT INTO relations (id, from_type, from_id, relation, to_type, to_id, status, source_event_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
            (rid, from_type, from_id, relation, to_type, to_id, source_event_id, now)
        )
        self.db.commit()

        return Relation(
            id=rid,
            from_type=from_type,
            from_id=from_id,
            relation=relation,
            to_type=to_type,
            to_id=to_id,
            status="active",
            source_event_id=source_event_id,
            created_at=now,
        )

    def invalidate(self, relation_id: str, source_event_id: Optional[str] = None) -> None:
        """Mark a relation as invalidated without deleting historical provenance."""
        self.db.execute(
            "UPDATE relations SET status = 'invalidated' WHERE id = ?",
            (relation_id,)
        )
        self.db.commit()

    def get_out_relations(
        self,
        from_type: str,
        from_id: str,
        relation: Optional[str] = None,
        status: str = "active"
    ) -> list[Relation]:
        """Fetch outgoing edges from an entity."""
        if relation:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE from_type = ? AND from_id = ? AND relation = ? AND status = ?",
                (from_type, from_id, relation, status)
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE from_type = ? AND from_id = ? AND status = ?",
                (from_type, from_id, status)
            )
        return [self._row_to_relation(r) for r in rows]

    def get_in_relations(
        self,
        to_type: str,
        to_id: str,
        relation: Optional[str] = None,
        status: str = "active"
    ) -> list[Relation]:
        """Fetch incoming edges to an entity."""
        if relation:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE to_type = ? AND to_id = ? AND relation = ? AND status = ?",
                (to_type, to_id, relation, status)
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM relations WHERE to_type = ? AND to_id = ? AND status = ?",
                (to_type, to_id, status)
            )
        return [self._row_to_relation(r) for r in rows]

    def _row_to_relation(self, row: Any) -> Relation:
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
