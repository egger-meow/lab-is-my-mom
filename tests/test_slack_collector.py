"""Tests for scoped, idempotent Slack ingestion."""
from pathlib import Path

import httpx

from master_os.collectors.slack import SlackCollector
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore


def test_slack_collector_ingests_scoped_messages_idempotently(tmp_path: Path):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["authorization"] == "Bearer test-token"
        assert request.url.params["channel"] == "C-LAB"
        return httpx.Response(
            200,
            json={
                "ok": True,
                "messages": [
                    {"type": "message", "user": "U-PROF", "text": "下週請準備 baseline。", "ts": "1788566400.000100"},
                    {"type": "message", "user": "U-STUDENT", "text": "收到", "ts": "1788566300.000050"},
                ],
                "has_more": False,
                "response_metadata": {"next_cursor": ""},
            },
        )

    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        collector = SlackCollector(db, events, token="test-token", client=client)

        first = collector.sync_channel("C-LAB", "lab-general")
        second = collector.sync_channel("C-LAB", "lab-general")

        assert first.ingested == 2
        assert second.ingested == 0
        rows = db.fetchall("SELECT * FROM events WHERE event_type='slack.message.received' ORDER BY occurred_at")
        assert len(rows) == 2
        assert rows[0]["actor_ref"] == "U-STUDENT"
        assert rows[1]["actor_ref"] == "U-PROF"
        assert "test-token" not in rows[1]["payload_json"]
        source = db.fetchone("SELECT * FROM sources WHERE external_ref='slack:C-LAB'")
        assert source is not None
        assert source["scope"] == "lab-general"
    finally:
        db.close()


def test_slack_collector_uses_latest_ingested_ts_as_incremental_oldest(tmp_path: Path):
    requested_oldest = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_oldest.append(request.url.params.get("oldest"))
        if len(requested_oldest) == 1:
            messages = [{"type": "message", "user": "U1", "text": "first", "ts": "1788566400.000100"}]
        else:
            messages = [{"type": "message", "user": "U2", "text": "new", "ts": "1788566500.000200"}]
        return httpx.Response(200, json={"ok": True, "messages": messages, "has_more": False, "response_metadata": {"next_cursor": ""}})

    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        collector = SlackCollector(
            db,
            events,
            token="test-token",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        collector.sync_channel("C-LAB")
        collector.sync_channel("C-LAB")

        assert requested_oldest[0] is None
        assert requested_oldest[1] == "1788566400.000100"
    finally:
        db.close()


def test_slack_collector_surfaces_api_error_without_advancing_state(tmp_path: Path):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "error": "missing_scope"})

    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        collector = SlackCollector(
            db,
            events,
            token="test-token",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        try:
            collector.sync_channel("C-LAB")
            assert False, "expected Slack API failure"
        except RuntimeError as exc:
            assert "missing_scope" in str(exc)

        assert db.fetchone("SELECT COUNT(*) AS n FROM events WHERE event_type='slack.message.received'")["n"] == 0
    finally:
        db.close()
