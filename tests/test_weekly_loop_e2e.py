"""End-to-end weekly research loop without fabricated semantic truth."""
from pathlib import Path

from master_os.agents.critic import MasterCritic
from master_os.agents.packet import WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event, rebuild_state
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner


def test_complete_weekly_research_loop(tmp_path: Path):
    db = MasterDatabase(tmp_path / "weekly_master.db")
    store = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root=tmp_path, events=store)
    relations = RelationGraph(db, events=store)
    critic = MasterCritic(db)
    runtime = AgentRuntime(db, store, artifacts, repo_root=tmp_path)
    builder = WorkPacketBuilder(db)
    meeting_agent = MeetingAgent(db, store, artifacts, relations, repo_root=tmp_path)
    planner = MasterPlanner(db)

    # 1. Evidence arrives. High-impact semantics remain proposals.
    transcript = """
    Prof: VDAR 可以先當 baseline。下次 meeting 記得把比較的表格帶過來，包含 accuracy 跟 cost。
    Student: 收到，我這週會把 VDAR baseline 實作完畢並跑初步評估。
    """
    ingested = meeting_agent.ingest_transcript("M-018", transcript)
    assert ingested["semantic_approval_ids"]
    assert db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"] == 0

    # 2. Human confirms only the obligation proposal.
    obligation_approval = None
    for approval_id in ingested["semantic_approval_ids"]:
        row = db.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
        if '"change_type": "obligation"' in row["action_payload_json"]:
            obligation_approval = approval_id
            break
    assert obligation_approval

    user_source = store.register_source("user", "User Cockpit", "weekly-e2e-user")
    approved = store.record_event(
        "approval.decided",
        user_source.id,
        {"id": obligation_approval, "status": "approved", "decision_note": "confirmed"},
        created_by="user_explicit",
    )
    apply_event(db, approved)
    obligation_id = meeting_agent.apply_semantic_approval(obligation_approval)
    assert obligation_id and obligation_id.startswith("O-")

    # 3. Planner gets a confirmed executable task linked to the obligation.
    task_event = store.record_event(
        "task.created",
        user_source.id,
        {
            "id": "T-weekly-baseline",
            "title": "Implement confirmed baseline comparison",
            "priority": "critical",
            "obligation_id": obligation_id,
            "agentability": "autonomous",
            "preferred_agent": "codex",
        },
        created_by="user_explicit",
    )
    apply_event(db, task_event)
    plan = planner.get_plan()
    assert plan.focus_action.task_id == "T-weekly-baseline"
    assert plan.focus_action.linked_obligation_id == obligation_id

    # 4. A test-only executor produces explicit artifacts and a candidate finding.
    workspace = tmp_path / "worktree-weekly"
    packet = builder.build_packet(
        "T-weekly-baseline",
        workspace_path=str(workspace),
        repo_name="routing-study",
    )

    def codex_test_executor(path: Path, pkt):
        results = path / "results"
        results.mkdir(parents=True, exist_ok=True)
        (results / "metrics.csv").write_text("method,acc,cost\nVDAR,0.860,0.150\n", encoding="utf-8")
        return {
            "exit_code": 0,
            "artifacts": ["results/metrics.csv"],
            "findings": [{"statement": "Test-run VDAR result is available for review", "confidence": 0.7}],
        }

    dispatch = runtime.dispatch_autonomous_job(packet, executor_func=codex_test_executor)
    assert dispatch["status"] == "completed"
    assert dispatch["task_status"] == "completed"
    assert dispatch["artifacts"]
    finding = db.fetchone("SELECT * FROM findings ORDER BY created_at DESC LIMIT 1")
    assert finding["status"] == "candidate"

    # 5. Meeting pack reflects actual state and does not manufacture demo metrics.
    pack = meeting_agent.generate_meeting_pack("M-019")
    assert "Test-run VDAR result is available for review" in pack
    assert "86.4" not in pack
    assert "17.8" not in pack

    # 6. External Slack write remains an approval, not an automatic send.
    slack_approval = meeting_agent.create_post_meeting_slack_approval(
        meeting_id="M-019",
        meeting_title="個人 Meeting M-019",
        date_str="2026-09-17",
        discussion_points=["檢視 baseline 結果"],
        next_commitments=["確認下一輪實驗"],
    )
    row = db.fetchone("SELECT * FROM approvals WHERE id = ?", (slack_approval,))
    assert row["status"] == "pending"
    assert row["action_type"] == "send_slack"

    # 7. Canonical history is sufficient to rebuild the materialized research state.
    before = {
        "obligations": db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"],
        "tasks": db.fetchone("SELECT COUNT(*) AS n FROM tasks")["n"],
        "artifacts": db.fetchone("SELECT COUNT(*) AS n FROM artifacts")["n"],
        "findings": db.fetchone("SELECT COUNT(*) AS n FROM findings")["n"],
        "relations": db.fetchone("SELECT COUNT(*) AS n FROM relations")["n"],
    }
    replayed = rebuild_state(db)
    assert replayed > 0
    after = {
        "obligations": db.fetchone("SELECT COUNT(*) AS n FROM obligations")["n"],
        "tasks": db.fetchone("SELECT COUNT(*) AS n FROM tasks")["n"],
        "artifacts": db.fetchone("SELECT COUNT(*) AS n FROM artifacts")["n"],
        "findings": db.fetchone("SELECT COUNT(*) AS n FROM findings")["n"],
        "relations": db.fetchone("SELECT COUNT(*) AS n FROM relations")["n"],
    }
    assert after == before

    # Health can use candidate evidence without pretending it is validated science.
    health = critic.evaluate_health()
    assert health.evidence_count >= 1
    db.close()
