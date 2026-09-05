"""Production bootstrap tests for the long-lived Master OS supervisor."""
from pathlib import Path

import pytest

from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.supervisor.bootstrap import build_supervisor, parse_slack_conversations


def test_parse_slack_conversations_is_explicit_and_scoped():
    assert parse_slack_conversations("C123:lab-general, D456:advisor-dm") == [
        ("C123", "lab-general"),
        ("D456", "advisor-dm"),
    ]
    with pytest.raises(ValueError):
        parse_slack_conversations("not-scoped")


def test_partial_slack_configuration_is_rejected(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        with pytest.raises(ValueError, match="SLACK_BOT_TOKEN"):
            build_supervisor(
                db,
                tmp_path,
                env={"MASTER_OS_SLACK_CONVERSATIONS": "C123:lab-general"},
            )
        with pytest.raises(ValueError, match="MASTER_OS_SLACK_CONVERSATIONS"):
            build_supervisor(
                db,
                tmp_path,
                env={"SLACK_BOT_TOKEN": "xoxb-secret"},
            )
    finally:
        db.close()


def test_supervisor_bootstrap_wires_scoped_slack_without_network(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    created: list[tuple[str, str]] = []

    class FakeSlackCollector:
        def __init__(self, _db, _events, token: str):
            assert _db is db
            created.append(("token", token))

        def sync_channel(self, channel_id: str, scope_name: str):
            created.append((channel_id, scope_name))
            return {"channel_id": channel_id, "seen": 2, "ingested": 1, "latest_ts": "42.0"}

    try:
        supervisor = build_supervisor(
            db,
            tmp_path,
            env={
                "SLACK_BOT_TOKEN": "xoxb-secret",
                "MASTER_OS_SLACK_CONVERSATIONS": "C123:lab-general,D456:advisor-dm",
            },
            slack_collector_factory=FakeSlackCollector,
        )

        assert sorted(supervisor.source_syncers) == ["slack:advisor-dm", "slack:lab-general"]
        first = supervisor.source_syncers["slack:lab-general"]()
        second = supervisor.source_syncers["slack:advisor-dm"]()
        assert first["ingested"] == 1
        assert second["channel_id"] == "D456"
        assert created == [
            ("token", "xoxb-secret"),
            ("C123", "lab-general"),
            ("D456", "advisor-dm"),
        ]
        assert all("xoxb-secret" not in key for key in supervisor.source_syncers)
    finally:
        db.close()


def test_supervisor_bootstrap_installs_real_advisor_pack_handler(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        supervisor = build_supervisor(db, tmp_path, env={})
        handler = supervisor.routine_handlers["meeting_agent"]
        result = handler(
            {
                "name": "Advisor Pre-Meeting Readiness & Pack",
                "context": {"meeting_id": "M-BOOTSTRAP"},
            }
        )

        assert result["status"] == "ok"
        assert result["meeting_id"] == "M-BOOTSTRAP"
        assert (tmp_path / "data" / "meeting_packs" / "M-BOOTSTRAP_pack.md").exists()
        assert db.fetchone("SELECT COUNT(*) AS n FROM artifacts WHERE artifact_type='meeting_pack'")["n"] == 1
    finally:
        db.close()


def test_supervisor_bootstrap_queues_post_meeting_slack_draft_from_event_evidence(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        agent = MeetingAgent(
            db,
            events,
            ArtifactRegistry(db, tmp_path, events=events),
            RelationGraph(db, events=events),
            tmp_path,
        )
        agent.ingest_transcript(
            "M-POST",
            """
            Prof: 下次 meeting 請準備好 baseline 比較表格。
            Student: 好，我這週會把 baseline 跑完並完成測試。
            """,
        )

        supervisor = build_supervisor(db, tmp_path, env={})
        handler = supervisor.routine_handlers["meeting_agent"]
        item = {
            "name": "Advisor Post-Meeting Digest to Slack",
            "context": {
                "event_type": "meeting.completed",
                "event_payload": {"id": "M-POST"},
            },
        }
        first = handler(item)
        second = handler(item)

        assert first["status"] == "ok"
        assert first["meeting_id"] == "M-POST"
        assert first["approval_id"] == second["approval_id"]
        assert db.fetchone("SELECT COUNT(*) AS n FROM approvals WHERE action_type='send_slack'")["n"] == 1
    finally:
        db.close()
