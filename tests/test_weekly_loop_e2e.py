"""End-to-End Vertical Slice Verification: One Real Research Week in Master OS.

Simulates the complete research loop at NYCU NLP Lab:
1. Previous advisor meeting transcript ingestion
2. Automatic extraction of commitments, obligations (VDAR comparison), tasks, decisions
3. Master Planner identifies the Critical Path
4. Autonomous dispatch of Codex inside an isolated worktree sandbox
5. Independent acceptance verification (acceptance criteria & artifact registration)
6. Derivation of findings and updating Failure Memory
7. Master Critic health & fake progress evaluation
8. Generation of compliant Meeting Pack outline for next meeting
9. Next meeting completion and generation of post-meeting Slack follow-up draft (awaiting approval)
10. Final approval decision and state updates
"""
from pathlib import Path
import pytest

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.relations import RelationGraph
from master_os.core.reducer import apply_event
from master_os.agents.critic import MasterCritic
from master_os.agents.packet import WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.scheduler.engine import SchedulerEngine


def test_complete_weekly_research_loop(tmp_path: Path):
    db_path = tmp_path / "weekly_master.db"
    db = MasterDatabase(db_path)
    store = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root=tmp_path)
    relations = RelationGraph(db)
    critic = MasterCritic(db)
    runtime = AgentRuntime(db, store, artifacts, repo_root=tmp_path)
    builder = WorkPacketBuilder(db)
    meeting_agent = MeetingAgent(db, store, artifacts, relations, repo_root=tmp_path)
    planner = MasterPlanner(db)
    scheduler = SchedulerEngine(db, store, critic)

    # ----------------------------------------------------
    # Step 1: Ingest Previous Advisor Meeting (M-018)
    # ----------------------------------------------------
    transcript_m18 = """
    顏老師: 上週看完 routing 相關 survey，你有想先做哪一個方向嗎？
    我: 老師好，我想針對多模型路由在 cost drift 下的表現做深入探討。目前看 VDAR 滿適合作為主要 baseline。
    顏老師: 好，那 VDAR 可以先當 baseline。下次 meeting 記得把比較的表格帶過來，包含 accuracy 跟 cost，我們主要針對數據討論 findings。
    我: 收到，我這週會把 VDAR baseline 實作完畢並跑初步評估。
    """
    res_m18 = meeting_agent.ingest_transcript("M-018", transcript_m18)
    assert res_m18["transcript_artifact_id"].startswith("A-")

    # Verify obligations created
    obs = db.fetchall("SELECT * FROM obligations WHERE meeting_id = 'M-018'")
    assert len(obs) == 1
    ob = obs[0]
    assert ob["severity"] == "critical"
    assert "VDAR baseline 比較表格" in ob["title"]

    # ----------------------------------------------------
    # Step 2: Planner identifies Critical Path Focus Action
    # ----------------------------------------------------
    plan = planner.get_plan()
    focus_task = plan.focus_action
    assert focus_task.task_id is not None
    assert "實作 VDAR baseline" in focus_task.title
    assert focus_task.linked_obligation_id == ob["id"]

    # ----------------------------------------------------
    # Step 3: Autonomous Codex Dispatch in Sandboxed Worktree
    # ----------------------------------------------------
    ws_path = tmp_path / "worktree-e2e-vdar"
    packet = builder.build_packet(focus_task.task_id, workspace_path=str(ws_path))

    # Executor simulating Codex code implementation + tests
    def codex_mock_executor(path: Path, pkt):
        results_dir = path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        (results_dir / "metrics.csv").write_text("method,acc,cost_reduction,latency_ms\nVDAR,0.860,0.150,155\n")

        reports_dir = path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "summary.md").write_text(
            "# VDAR Baseline Evaluation\nBaseline replicated on MMLU subset with 86% accuracy."
        )

        return {
            "exit_code": 0,
            "artifacts": ["results/metrics.csv", "reports/summary.md"],
            "findings": [
                {"statement": "VDAR baseline achieved 86.0% accuracy with 15.0% cost reduction on test benchmark", "confidence": 0.92}
            ],
        }

    dispatch_res = runtime.dispatch_autonomous_job(packet, executor_func=codex_mock_executor)
    assert dispatch_res["status"] == "completed"
    assert dispatch_res["task_status"] == "completed"
    assert len(dispatch_res["artifacts"]) == 2

    # Verify task status is now completed
    task_row = db.fetchone("SELECT * FROM tasks WHERE id = ?", (focus_task.task_id,))
    assert task_row["status"] == "completed"

    # ----------------------------------------------------
    # Step 4: Verify Findings & Evidence Accumulation
    # ----------------------------------------------------
    findings = db.fetchall("SELECT * FROM findings")
    assert len(findings) == 1
    assert "VDAR baseline achieved 86.0%" in findings[0]["statement"]

    # Master Health Check: Velocity should reflect real evidence
    health = critic.evaluate_health()
    assert health.fake_progress_warning is False
    assert health.evidence_count >= 1
    assert health.research_velocity > 1.0

    # ----------------------------------------------------
    # Step 5: Generate Next Meeting Pack (M-019)
    # ----------------------------------------------------
    pack_content = meeting_agent.generate_meeting_pack("M-019")
    assert "第一階段：進度與承諾回顧" in pack_content
    assert "第二階段：今日討論事項" in pack_content
    assert "第三階段：實驗進度與 Findings 報告" in pack_content
    assert "VDAR baseline achieved 86.0%" in pack_content

    # Mark obligation satisfied
    system_source = store.register_source("system", "Master System", "system")
    sat_event = store.record_event(
        "obligation.satisfied",
        system_source.id,
        {"id": ob["id"]},
    )
    apply_event(db, sat_event)
    ob_updated = db.fetchone("SELECT * FROM obligations WHERE id = ?", (ob["id"],))
    assert ob_updated["status"] == "satisfied"

    # ----------------------------------------------------
    # Step 6: Post-Meeting Slack Follow-up Approval Request
    # ----------------------------------------------------
    ap_id = meeting_agent.create_post_meeting_slack_approval(
        meeting_id="M-019",
        meeting_title="個人 Meeting M-019",
        date_str="2026-09-17",
        discussion_points=[
            "報告 VDAR baseline 重現數據 (86% accuracy, 15% cost reduction)",
            "確認在 cost drift 下加入動態信心校準以解決 F-27 歷史失真問題",
        ],
        next_commitments=[
            "實作 Selective Margin Router 並與 VDAR 比較",
            "進行下一階段 cross-model 評估實驗",
        ],
    )

    approval_row = db.fetchone("SELECT * FROM approvals WHERE id = ?", (ap_id,))
    assert approval_row["status"] == "pending"
    assert approval_row["action_type"] == "send_slack"
    assert "VDAR baseline 重現數據" in approval_row["action_payload_json"]

    # ----------------------------------------------------
    # Step 7: User Approves Slack Follow-up in Cockpit
    # ----------------------------------------------------
    user_source = store.register_source("user", "User Cockpit", "cockpit-ui")
    decide_event = store.record_event(
        "approval.decided",
        user_source.id,
        {"id": ap_id, "status": "approved", "decision_note": "確認無誤，傳送給老師"},
        created_by="user_explicit",
    )
    apply_event(db, decide_event)

    ap_final = db.fetchone("SELECT * FROM approvals WHERE id = ?", (ap_id,))
    assert ap_final["status"] == "approved"

    db.close()
