"""Tests for Master OS Intelligence Layer (Meeting Agent, Planner, Scheduler)."""
from pathlib import Path

import pytest

from master_os.agents.critic import MasterCritic
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.scheduler.engine import SchedulerEngine


@pytest.fixture
def intel_setup(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test_intel.db")
    store = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root=tmp_path, events=store)
    relations = RelationGraph(db, events=store)
    critic = MasterCritic(db)
    meeting_agent = MeetingAgent(db, store, artifacts, relations, repo_root=tmp_path)
    planner = MasterPlanner(db)
    scheduler = SchedulerEngine(db, store, critic)
    yield db, store, artifacts, relations, meeting_agent, planner, scheduler
    db.close()


def test_meeting_agent_transcript_ingestion_queues_semantics_for_confirmation(intel_setup):
    db, _, _, _, agent, _, _ = intel_setup
    transcript = """
    Prof: VDAR 可以先當 baseline。下次 meeting 記得把比較表格帶過來，包含 accuracy 跟 cost。
    Student: 好，我這週會把 baseline 跑出來並驗證測試。
    """

    result = agent.ingest_transcript("M-20260910", transcript)
    assert result["transcript_artifact_id"].startswith("A-")
    assert result["semantic_approval_ids"]

    # Tier-2 meanings are not silently promoted to research truth.
    assert db.fetchone("SELECT COUNT(*) AS n FROM decisions")["n"] == 0
    assert db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"] == 0
    assert db.fetchone("SELECT COUNT(*) AS n FROM tasks")["n"] == 0

    approvals = db.fetchall("SELECT * FROM approvals WHERE action_type='confirm_semantic_change'")
    assert len(approvals) >= 2


def test_approved_meeting_semantic_materializes_once(intel_setup):
    db, store, _, relations, agent, _, _ = intel_setup
    result = agent.ingest_transcript(
        "M-20260910",
        "Prof: 下次 meeting 請準備好 VDAR baseline 數據。",
    )
    approval_id = result["semantic_approval_ids"][0]

    event = store.record_event(
        "approval.decided",
        store.register_source("user", "test user", "test-user").id,
        {"id": approval_id, "status": "approved", "decision_note": "confirmed"},
        created_by="user_explicit",
    )
    from master_os.core.reducer import apply_event
    apply_event(db, event)

    entity_id = agent.apply_semantic_approval(approval_id)
    assert entity_id and entity_id.startswith("O-")
    assert db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"] == 1
    assert agent.apply_semantic_approval(approval_id) == entity_id
    assert db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"] == 1
    assert relations.get_out_relations("approval", approval_id, "materialized_as")


def test_meeting_pack_never_invents_demo_metrics(intel_setup):
    _, _, _, _, agent, _, _ = intel_setup
    pack = agent.generate_meeting_pack("M-20260917")
    assert "第一階段：進度與承諾回顧" in pack
    assert "第二階段：今日討論事項" in pack
    assert "第三階段：實驗進度與 Findings 報告" in pack
    assert "尚無可引用 Finding" in pack
    assert "86.4" not in pack
    assert "17.8" not in pack


def test_post_meeting_slack_approval(intel_setup):
    db, _, _, _, agent, _, _ = intel_setup
    approval_id = agent.create_post_meeting_slack_approval(
        meeting_id="M-20260910",
        meeting_title="個人 Meeting",
        date_str="2026-09-10",
        discussion_points=["確立評估標準"],
        next_commitments=["完成測試"],
    )
    row = db.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
    assert row["action_type"] == "send_slack"
    assert row["status"] == "pending"


def test_master_planner_prioritizes_confirmed_obligation(intel_setup):
    db, store, _, _, _, planner, _ = intel_setup
    from master_os.core.reducer import apply_event

    source = store.register_source("user", "test", "planner-test")
    ob = store.record_event(
        "obligation.created",
        source.id,
        {"id": "O-critical", "title": "Bring evidence to advisor", "severity": "critical"},
    )
    apply_event(db, ob)
    task = store.record_event(
        "task.created",
        source.id,
        {"id": "T-critical", "title": "Prepare evidence", "priority": "critical", "obligation_id": "O-critical"},
    )
    apply_event(db, task)

    plan = planner.get_plan()
    assert plan.focus_action.task_id == "T-critical"
    assert plan.focus_action.linked_obligation_id == "O-critical"


def test_scheduler_engine_default_routines(intel_setup):
    _, _, _, _, _, _, scheduler = intel_setup
    schedules = scheduler.list_schedules()
    assert len(schedules) >= 5
    names = [s["name"] for s in schedules]
    assert "Weekly Seminar Readiness" in names
    assert "Advisor Pre-Meeting Readiness & Pack" in names
    assert "NCHC & API Resource Burn Watchdog" in names

    result = scheduler.trigger_routine("Weekly Research Progress & Critic")
    assert result["status"] == "ok"
    assert "health_report" in result
