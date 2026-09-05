"""Single atomic write pipeline for canonical events and materialized state."""
from __future__ import annotations

from typing import Any, Callable, Optional

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import Event
from master_os.core.reducer import apply_event


Reducer = Callable[..., None]


class DomainCommandBus:
    """Append one canonical event and reduce it in the same SQLite transaction.

    Adapters and agents should use this boundary for domain mutations instead of
    independently calling ``record_event`` and ``apply_event``. If materialization
    fails, the event append is rolled back too. Deduplicated commands return their
    existing canonical event without replaying a reducer or performing side effects.
    """

    def __init__(
        self,
        db: MasterDatabase,
        events: Optional[EventStore] = None,
        *,
        reducer: Reducer = apply_event,
    ) -> None:
        self.db = db
        self.events = events or EventStore(db)
        self.reducer = reducer

    def emit(
        self,
        event_type: str,
        source_id: str,
        payload: dict[str, Any],
        *,
        occurred_at: Optional[str] = None,
        external_id: Optional[str] = None,
        dedup_key: Optional[str] = None,
        actor_ref: Optional[str] = None,
        raw_ref: Optional[str] = None,
        raw_content: Optional[str | bytes] = None,
        created_by: str = "system",
    ) -> Event:
        try:
            self.db.execute("BEGIN IMMEDIATE")

            if dedup_key:
                existing = self.db.fetchone("SELECT id FROM events WHERE dedup_key = ?", (dedup_key,))
                if existing:
                    # EventStore owns row -> Event decoding. record_event performs no
                    # insert when the dedup key already exists.
                    event = self.events.record_event(
                        event_type,
                        source_id,
                        payload,
                        occurred_at=occurred_at,
                        external_id=external_id,
                        dedup_key=dedup_key,
                        actor_ref=actor_ref,
                        raw_ref=raw_ref,
                        raw_content=raw_content,
                        created_by=created_by,
                        commit=False,
                    )
                    self.db.commit()
                    return event

            event = self.events.record_event(
                event_type,
                source_id,
                payload,
                occurred_at=occurred_at,
                external_id=external_id,
                dedup_key=dedup_key,
                actor_ref=actor_ref,
                raw_ref=raw_ref,
                raw_content=raw_content,
                created_by=created_by,
                commit=False,
            )
            self.reducer(self.db, event, commit=False)
            self.db.commit()
            return event
        except Exception:
            self.db.rollback()
            raise
