"""Append-only Event Store for Master OS."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.models import Event, Source, generate_id, utc_now


class EventStore:
    """Manages sources and append-only event ingestion."""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def register_source(
        self,
        source_type: str,
        name: str,
        external_ref: str,
        scope: str = "default",
        authority_class: str = "verified_source",
        source_id: Optional[str] = None,
    ) -> Source:
        """Register or get a data source."""
        existing = self.db.fetchone(
            "SELECT * FROM sources WHERE type = ? AND external_ref = ?",
            (source_type, external_ref)
        )
        if existing:
            return Source(
                id=existing["id"],
                type=existing["type"],
                name=existing["name"],
                external_ref=existing["external_ref"],
                scope=existing["scope"],
                enabled=bool(existing["enabled"]),
                authority_class=existing["authority_class"],
                created_at=existing["created_at"],
                last_synced_at=existing["last_synced_at"],
            )

        sid = source_id or generate_id("S-")
        now = utc_now()
        self.db.execute(
            """INSERT INTO sources (id, type, name, external_ref, scope, enabled, authority_class, created_at, last_synced_at)
               VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)""",
            (sid, source_type, name, external_ref, scope, authority_class, now, now)
        )
        self.db.commit()
        return Source(
            id=sid,
            type=source_type,
            name=name,
            external_ref=external_ref,
            scope=scope,
            enabled=True,
            authority_class=authority_class,
            created_at=now,
            last_synced_at=now,
        )

    def record_event(
        self,
        event_type: str,
        source_id: str,
        payload: dict[str, Any],
        occurred_at: Optional[str] = None,
        external_id: Optional[str] = None,
        dedup_key: Optional[str] = None,
        actor_ref: Optional[str] = None,
        raw_ref: Optional[str] = None,
        raw_content: Optional[str | bytes] = None,
        created_by: str = "system",
        commit: bool = True,
    ) -> Event:
        """Record an immutable domain event.

        ``commit=False`` is reserved for command handlers that append the event
        and materialize its state in one caller-owned transaction.
        """
        if dedup_key:
            existing = self.db.fetchone("SELECT * FROM events WHERE dedup_key = ?", (dedup_key,))
            if existing:
                return self._row_to_event(existing)

        raw_hash = None
        if raw_content is not None:
            raw_bytes = raw_content.encode("utf-8") if isinstance(raw_content, str) else raw_content
            raw_hash = hashlib.sha256(raw_bytes).hexdigest()

        eid = generate_id("EV-")
        now = utc_now()
        occ = occurred_at or now

        payload_json = json.dumps(payload, ensure_ascii=False)
        self.db.execute(
            """INSERT INTO events (id, event_type, source_id, occurred_at, ingested_at, external_id,
                                  dedup_key, actor_ref, raw_ref, raw_hash, payload_json, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (eid, event_type, source_id, occ, now, external_id, dedup_key, actor_ref, raw_ref, raw_hash, payload_json, created_by)
        )
        if commit:
            self.db.commit()

        return Event(
            id=eid,
            event_type=event_type,
            source_id=source_id,
            occurred_at=occ,
            ingested_at=now,
            external_id=external_id,
            dedup_key=dedup_key,
            actor_ref=actor_ref,
            raw_ref=raw_ref,
            raw_hash=raw_hash,
            payload=payload,
            created_by=created_by,
        )

    def get_events(self, after_id: Optional[str] = None, limit: int = 1000) -> list[Event]:
        """Fetch chronological events without losing same-timestamp siblings."""
        if after_id:
            anchor = self.db.fetchone("SELECT occurred_at, rowid AS event_rowid FROM events WHERE id = ?", (after_id,))
            if not anchor:
                raise ValueError(f"Event cursor not found: {after_id}")
            rows = self.db.fetchall(
                """SELECT * FROM events
                   WHERE occurred_at > ? OR (occurred_at = ? AND rowid > ?)
                   ORDER BY occurred_at ASC, rowid ASC LIMIT ?""",
                (anchor["occurred_at"], anchor["occurred_at"], anchor["event_rowid"], limit),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM events ORDER BY occurred_at ASC, rowid ASC LIMIT ?",
                (limit,)
            )
        return [self._row_to_event(r) for r in rows]

    def _row_to_event(self, row: Any) -> Event:
        return Event(
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
