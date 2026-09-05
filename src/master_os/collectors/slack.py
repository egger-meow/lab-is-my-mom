"""Scoped Slack history collector.

The collector only reads explicitly configured conversation IDs. It records raw
Slack messages as Tier-0 canonical observations and leaves semantic
interpretation to later Master OS stages.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import utc_now


@dataclass(frozen=True)
class SlackSyncResult:
    channel_id: str
    seen: int
    ingested: int
    latest_ts: Optional[str]


class SlackCollector:
    """Incrementally ingest one authorized Slack conversation via Web API."""

    API_URL = "https://slack.com/api/conversations.history"

    def __init__(
        self,
        db: MasterDatabase,
        events: EventStore,
        token: str,
        client: Optional[httpx.Client] = None,
        page_limit: int = 200,
    ) -> None:
        if not token.strip():
            raise ValueError("Slack token is required")
        self.db = db
        self.events = events
        self.token = token.strip()
        self.client = client or httpx.Client(timeout=20.0)
        self.page_limit = max(1, min(page_limit, 200))

    def sync_channel(self, channel_id: str, scope_name: Optional[str] = None) -> SlackSyncResult:
        """Fetch messages newer than the latest persisted message for a channel."""
        channel_id = channel_id.strip()
        if not channel_id:
            raise ValueError("Slack channel/conversation ID is required")

        scope = scope_name or channel_id
        source = self.events.register_source(
            "slack_channel",
            f"Slack {scope}",
            f"slack:{channel_id}",
            scope=scope,
            authority_class="verified_source",
        )
        oldest = self._latest_external_ts(source.id)
        cursor: Optional[str] = None
        seen = 0
        ingested = 0
        latest_ts = oldest

        while True:
            params: dict[str, Any] = {"channel": channel_id, "limit": self.page_limit}
            if oldest:
                params["oldest"] = oldest
                params["inclusive"] = "false"
            if cursor:
                params["cursor"] = cursor

            response = self.client.get(
                self.API_URL,
                params=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                raise RuntimeError(f"Slack API rate limited; retry after {retry_after} seconds")
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(f"Slack API error: {body.get('error', 'unknown_error')}")

            messages = body.get("messages") or []
            seen += len(messages)
            for message in messages:
                ts = str(message.get("ts") or "").strip()
                if not ts:
                    continue
                dedup_key = f"slack:{channel_id}:{ts}"
                existed = self.db.fetchone("SELECT id FROM events WHERE dedup_key = ?", (dedup_key,)) is not None
                event = self.events.record_event(
                    event_type="slack.message.received",
                    source_id=source.id,
                    payload={
                        "channel_id": channel_id,
                        "message": message,
                    },
                    occurred_at=self._slack_ts_to_iso(ts),
                    external_id=ts,
                    dedup_key=dedup_key,
                    actor_ref=message.get("user") or message.get("bot_id"),
                    raw_content=self._canonical_message_bytes(message),
                    created_by="slack_collector",
                )
                if not existed:
                    ingested += 1
                if latest_ts is None or float(ts) > float(latest_ts):
                    latest_ts = ts

            metadata = body.get("response_metadata") or {}
            cursor = str(metadata.get("next_cursor") or "").strip() or None
            if not cursor:
                break

        self.db.execute("UPDATE sources SET last_synced_at = ? WHERE id = ?", (utc_now(), source.id))
        self.db.commit()
        return SlackSyncResult(channel_id=channel_id, seen=seen, ingested=ingested, latest_ts=latest_ts)

    def _latest_external_ts(self, source_id: str) -> Optional[str]:
        row = self.db.fetchone(
            """SELECT external_id FROM events
               WHERE source_id = ? AND event_type = 'slack.message.received' AND external_id IS NOT NULL
               ORDER BY CAST(external_id AS REAL) DESC LIMIT 1""",
            (source_id,),
        )
        return str(row["external_id"]) if row else None

    @staticmethod
    def _slack_ts_to_iso(ts: str) -> str:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _canonical_message_bytes(message: dict[str, Any]) -> bytes:
        import json

        return json.dumps(message, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
