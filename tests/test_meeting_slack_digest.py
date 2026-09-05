"""Evidence-backed post-meeting Slack draft regressions."""
import json
from pathlib import Path

from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent


def test_post_meeting_digest_is_source_backed_and_idempotent(tmp_path: Path):
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
            "M-DIGEST",
            """
            Prof: 下次 meeting 請準備好 VDAR baseline 數據與比較表格。
            Student: 好，我這週會把 baseline 跑出來並完成測試。
            """,
        )

        first = agent.create_post_meeting_slack_approval_from_evidence("M-DIGEST")
        second = agent.create_post_meeting_slack_approval_from_evidence("M-DIGEST")
        assert first == second

        rows = db.fetchall("SELECT * FROM approvals WHERE action_type='send_slack'")
        assert len(rows) == 1
        payload = json.loads(rows[0]["action_payload_json"])
        assert payload["meeting_id"] == "M-DIGEST"
        assert payload["channel"] == "advisor-dm"
        assert "下次 meeting 請準備好 VDAR baseline 數據與比較表格" in payload["text"]
        assert "我這週會把 baseline 跑出來並完成測試" in payload["text"]
        assert "86.4" not in payload["text"]
        assert "17.8" not in payload["text"]
    finally:
        db.close()
