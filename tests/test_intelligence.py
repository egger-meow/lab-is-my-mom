"""Tests for Master OS Intelligence Layer (Meeting Agent, Planner, Scheduler)."""
from pathlib import Path
import pytest

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.relations import RelationGraph
from master_os.agents.critic import MasterCritic
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.scheduler.engine import SchedulerEngine


@pytest.fixture
def intel_setup(tmp_path: Path):
    db_path = tmp_path / "test_intel.db"
    db = MasterDatabase(db_path)
    store = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root=tmp_path)
    relations = RelationGraph(db)
    critic = MasterCritic(db)
    meeting_agent = MeetingAgent(db, store, artifacts, relations, repo_root=tmp_path)
    planner = MasterPlanner(db)
    scheduler = SchedulerEngine(db, store, critic)
    yield db, store, artifacts, relations, meeting_agent, planner, scheduler
    db.close()


def test_meeting_agent_transcript_ingestion(intel_setup):
    db, _, _, relations, agent, _, _ = intel_setup

    sample_transcript = """
    Prof: 上週你看的 paper 怎麼樣？
    Student: 我看了 selective router 的架構，想先用 VDAR 當 baseline。
    Prof: VDAR 可以先當 baseline，那下次 meeting 記得把比較的表格帶過來，包含 accuracy 跟 cost。
    Student: 好的，我這週會把 baseline 跑出來並驗證測試。
    """

    res = agent.ingest_transcript("M-20260910", sample_transcript)
    assert res["transcript_artifact_id"].startswith("A-")

    # Check decisions
    decisions = db.fetchall("SELECT * FROM decisions")
    assert len(decisions) >= 1
    assert "VDAR" in decisions[0]["statement"]

    # Check obligations
    obs = db.fetchall("SELECT * FROM obligations")
    assert len(obs) >= 1
    assert "VDAR baseline 比較表格" in obs[0]["title"]
    assert obs[0]["severity"] == "critical"

    # Check tasks created from obligation
    tasks = db.fetchall("SELECT * FROM tasks")
    assert len(tasks) >= 2
    assert any("實作 VDAR baseline" in t["title"] for t in tasks)

    # Check relations graph
    m_edges = relations.get_out_relations("meeting", "M-20260910")
    assert len(m_edges) >= 1
    assert m_edges[0].relation == "created"


def test_meeting_pack_generation(intel_setup):
    _, _, _, _, agent, _, _ = intel_setup
    sample_transcript = "Prof: 下次 meeting 請準備好 VDAR baseline 數據。"
    agent.ingest_transcript("M-20260910", sample_transcript)

    pack_md = agent.generate_meeting_pack("M-20260917")
    assert "# 個人 Meeting 報告簡報大綱 (Meeting Pack)" in pack_md
    assert "第一階段：進度與承諾回顧" in pack_md
    assert "第二階段：今日討論事項" in pack_md
    assert "第三階段：實驗進度與 Findings 報告" in pack_md
    assert "VDAR" in pack_md


def test_post_meeting_slack_approval(intel_setup):
    db, _, _, _, agent, _, _ = intel_setup
    ap_id = agent.create_post_meeting_slack_approval(
        meeting_id="M-20260910",
        meeting_title="個人 Meeting",
        date_str="2026-09-10",
        discussion_points=["確立 VDAR baseline 評估標準", "討論 cost drift 模擬環境"],
        next_commitments=["完成 baseline 測試程式", "產出 metrics 表格"],
    )

    assert ap_id.startswith("AP-")
    ap_row = db.fetchone("SELECT * FROM approvals WHERE id = ?", (ap_id,))
    assert ap_row["action_type"] == "send_slack"
    assert ap_row["status"] == "pending"
    assert "實驗室需知規定" in ap_row["reason"]


def test_master_planner_critical_path(intel_setup):
    _, _, _, _, agent, planner, _ = intel_setup
    sample_transcript = "Prof: 下次 meeting 把 baseline 跑出來。"
    agent.ingest_transcript("M-20260910", sample_transcript)

    plan = planner.get_plan()
    assert plan.focus_action.task_id is not None
    assert "實作 VDAR baseline" in plan.focus_action.title
    assert "Priority: CRITICAL" in plan.focus_action.why
    assert len(plan.critical_obligations) >= 1


def test_scheduler_engine_default_routines(intel_setup):
    _, _, _, _, _, _, scheduler = intel_setup
    schedules = scheduler.list_schedules()
    assert len(schedules) >= 5

    names = [s["name"] for s in schedules]
    assert "Weekly Seminar Readiness" in names
    assert "Advisor Pre-Meeting Readiness & Pack" in names
    assert "NCHC & API Resource Burn Watchdog" in names

    # Trigger critic routine
    res = scheduler.trigger_routine("Weekly Research Progress & Critic")
    assert res["status"] == "ok"
    assert "health_report" in res
