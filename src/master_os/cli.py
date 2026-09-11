"""Command-line interface for Master OS (lab-is-my-mom)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from master_os.agents.critic import MasterCritic
from master_os.agents.executors import build_local_executors
from master_os.agents.packet import WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.relations import RelationGraph
from master_os.intelligence.meeting_agent import MeetingAgent
from master_os.intelligence.planner import MasterPlanner
from master_os.supervisor.autostart import AutostartManager
from master_os.supervisor.backup import BackupManager
from master_os.supervisor.bootstrap import build_supervisor
from master_os.supervisor.doctor import MasterDoctor
from master_os.web.api import create_app


def get_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parent.parent.parent
    db_path = repo_root / ".master-os" / "master.db"
    return repo_root, db_path


def run_start(
    web_db: MasterDatabase,
    repo_root: Path,
    *,
    host: str,
    port: int,
    supervisor_builder: Callable[..., Any] = build_supervisor,
    app_builder: Callable[..., Any] = create_app,
    executor_builder: Callable[[], dict[str, Any]] = build_local_executors,
    server_runner: Optional[Callable[..., Any]] = None,
) -> None:
    """Run the Web Cockpit and supervisor as one local process.

    The web server and supervisor deliberately use separate SQLite connections.
    WAL coordinates them safely while avoiding concurrent threads sharing one
    ``sqlite3.Connection`` object.
    """
    if server_runner is None:
        import uvicorn

        server_runner = uvicorn.run

    root = repo_root.resolve()
    supervisor_db = MasterDatabase(web_db.db_path)
    supervisor = None
    started = False
    try:
        supervisor = supervisor_builder(supervisor_db, root)
        app = app_builder(web_db, root, agent_executors=executor_builder())
        supervisor.start()
        started = True
        server_runner(app, host=host, port=port)
    finally:
        if supervisor is not None and started:
            supervisor.stop()
        supervisor_db.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="master-os", description="Master OS: Local-First Autonomous Runtime for NYCU NLP Lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_start = subparsers.add_parser("start", help="Start the Master OS local server, supervisor, and Web Cockpit")
    p_start.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host (default: loopback; use Tailscale Serve for remote access)",
    )
    p_start.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")

    subparsers.add_parser("status", help="Show current research velocity, critical path, and obligations")
    subparsers.add_parser("doctor", help="Run database integrity, worktree, and research health diagnostics")
    subparsers.add_parser("backup", help="Create an atomic SQLite snapshot")
    subparsers.add_parser("rebuild-state", help="Deterministically rebuild current state from canonical event history")

    p_autostart = subparsers.add_parser("autostart", help="Manage boot/login startup for the Master OS mothership")
    autostart_sub = p_autostart.add_subparsers(dest="autostart_cmd", required=True)
    autostart_sub.add_parser("install", help="Install and start user-scoped autostart")
    autostart_sub.add_parser("status", help="Show whether autostart is installed")
    autostart_sub.add_parser("uninstall", help="Disable and remove user-scoped autostart")

    p_meeting = subparsers.add_parser("meeting", help="Meeting operations (ingest, pack)")
    meeting_sub = p_meeting.add_subparsers(dest="meeting_cmd", required=True)
    p_ingest = meeting_sub.add_parser("ingest", help="Ingest a meeting transcript")
    p_ingest.add_argument("meeting_id", help="Meeting ID (e.g. M-20260910)")
    p_ingest.add_argument("transcript_file", type=Path, help="Path to transcript text file")
    p_pack = meeting_sub.add_parser("pack", help="Generate meeting presentation pack")
    p_pack.add_argument("meeting_id", help="Target meeting ID (e.g. M-20260917)")

    p_document = subparsers.add_parser("document", help="Document and presentation management")
    doc_sub = p_document.add_subparsers(dest="doc_cmd", required=True)
    p_doc_add = doc_sub.add_parser("add", help="Add/store a document or presentation")
    p_doc_add.add_argument("file_path", type=Path, help="Path to PDF or document file")
    p_doc_add.add_argument("--date", help="Date in YYYY-MM-DD format (defaults to today or filename prefix)")
    p_doc_add.add_argument("--ingest", action="store_true", help="Immediately ingest and update local DB with extracted obligations and tasks")
    p_doc_list = doc_sub.add_parser("list", help="List stored documents and presentations")
    p_doc_prompt = doc_sub.add_parser("prompt", help="Generate ready-to-copy Agent Prompt for a document")
    p_doc_prompt.add_argument("filename", help="Filename of the stored document")
    p_doc_ingest = doc_sub.add_parser("ingest", help="Ingest document: extract text via PyMuPDF C++, parse obligations & tasks, and update local DB")
    p_doc_ingest.add_argument("filename", help="Filename of the stored document")

    p_dispatch = subparsers.add_parser("dispatch", help="Dispatch a confirmed autonomous task to the local Codex CLI")
    p_dispatch.add_argument("task_id", help="Task ID (e.g. T-193)")

    args = parser.parse_args()
    repo_root, db_path = get_paths()
    db = MasterDatabase(db_path)

    try:
        if args.command == "start":
            print(f"啟動 Master OS 本地 Mothership ({args.host}:{args.port})...")
            print(f"Web Cockpit: http://127.0.0.1:{args.port}")
            print("Supervisor: scheduler + configured source collectors will run in-process.")
            if args.host == "127.0.0.1":
                print("外出連線建議使用 Tailscale Serve 代理此 loopback 服務，不需暴露整個 LAN。")
            run_start(db, repo_root, host=args.host, port=args.port)

        elif args.command == "status":
            planner = MasterPlanner(db)
            critic = MasterCritic(db)
            plan = planner.get_plan()
            health = critic.evaluate_health()

            print("==================================================")
            print("          MASTER OS · NYCU NLP LAB STATUS         ")
            print("==================================================")
            print(f"研究動力評分 (Velocity): {health.research_velocity}/10.0")
            print(f"實證累積 (Evidence): {health.evidence_count} 件 (Findings: {health.findings_count}, Exps: {health.completed_experiments})")
            print(f"狀態: {health.warning_message}")

            print("\n【當前最重要行動】")
            fa = plan.focus_action
            print(f"• {fa.title}")
            print(f"  原因: {fa.why}")
            print(f"  建議代理: {fa.suggested_agent.upper()} (預估 ~{fa.estimated_minutes} 分鐘)")

            print("\n【關鍵生存義務】")
            if plan.critical_obligations:
                for ob in plan.critical_obligations:
                    print(f"• [{ob['severity'].upper()}] {ob['title']} ({ob['status']})")
            else:
                print("• (目前無緊急待滿足義務)")
            print("==================================================")

        elif args.command == "doctor":
            doctor = MasterDoctor(db, repo_root)
            diag = doctor.run_diagnostics()
            print("Master OS 系統診斷報告：")
            print(f"整體狀態: {diag['status'].upper()}")
            print(f"資料庫完整性: {diag['checks']['database']['integrity_message']} (外鍵違規: {diag['checks']['database']['foreign_key_violations']})")
            print(f"歷史事件: {diag['stats']['total_events']}, Sources: {diag['stats']['total_sources']}, Artifacts: {diag['stats']['total_artifacts']}")
            if diag["warnings"]:
                print("\n警告事項：")
                for warning in diag["warnings"]:
                    print(f"• {warning}")

        elif args.command == "backup":
            snapshot = BackupManager(db, repo_root).create_snapshot()
            print(f"資料庫快照已建立：{snapshot}")

        elif args.command == "rebuild-state":
            count = BackupManager(db, repo_root).rebuild_current_state()
            print(f"已從 {count} 筆 canonical events 確定性還原 Current State。")

        elif args.command == "autostart":
            manager = AutostartManager(repo_root)
            if args.autostart_cmd == "install":
                result = manager.install()
                print(f"Master OS autostart 已安裝：{result['kind']}")
            elif args.autostart_cmd == "status":
                result = manager.status()
                state = "已安裝" if result["installed"] else "未安裝"
                print(f"Master OS autostart 狀態：{state} ({result['kind']})")
            else:
                result = manager.uninstall()
                print(f"Master OS autostart 已移除：{result['kind']}")

        elif args.command == "meeting":
            events = EventStore(db)
            artifacts = ArtifactRegistry(db, repo_root, events=events)
            relations = RelationGraph(db, events=events)
            agent = MeetingAgent(db, events, artifacts, relations, repo_root)

            if args.meeting_cmd == "ingest":
                if not args.transcript_file.exists():
                    print(f"檔案不存在: {args.transcript_file}", file=sys.stderr)
                    sys.exit(1)
                text = args.transcript_file.read_text(encoding="utf-8")
                result = agent.ingest_transcript(args.meeting_id, text, str(args.transcript_file.name))
                print(f"逐字稿已保存。Artifact: {result['transcript_artifact_id']}")
                approvals = result.get("semantic_approval_ids", [])
                if approvals:
                    print(f"偵測到 {len(approvals)} 個高影響語意候選，已送到 Needs You，尚未寫成研究真相。")
                else:
                    print("未偵測到需要確認的高影響語意變更。")

            elif args.meeting_cmd == "pack":
                pack = agent.generate_meeting_pack(args.meeting_id)
                print(f"成功產出 {args.meeting_id} Meeting Pack：\n")
                print(pack[:500] + "...\n(完整檔案位於 data/meeting_packs/)")

        elif args.command == "document":
            from master_os.documents import ingest_document_to_db, list_documents, save_document
            events = EventStore(db)
            artifacts = ArtifactRegistry(db, repo_root, events=events)
            if args.doc_cmd == "add":
                src = args.file_path.resolve()
                if not src.exists():
                    print(f"檔案不存在: {args.file_path}", file=sys.stderr)
                    sys.exit(1)
                content = src.read_bytes()
                res = save_document(repo_root, src.name, content, date_str=args.date, artifacts=artifacts)
                print(f"成功儲存文件: {res['filename']} ({res['size_bytes']} bytes)")
                print(f"路徑: {res['path']}")
                if res.get("engine"):
                    print(f"解析引擎: {res['engine']} ({res.get('pages', 1)} 頁, {res.get('chars', 0)} 字)")
                if res.get("artifact_id"):
                    print(f"Artifact ID: {res['artifact_id']}")
                if getattr(args, "ingest", False):
                    print(f"\n🚀 自動派遣 Agent 解析並更新 Master OS 本地資料庫...")
                    ingest_res = ingest_document_to_db(repo_root, res["filename"], db=db, events=events)
                    print(f"   建立 {ingest_res['obligations_created']} 個 Obligations、{ingest_res['tasks_created']} 個 Tasks")
                    print(f"   Agent Run 紀錄: {ingest_res['run_id']}")
                    print("✅ 本地資料庫更新完成！")
                else:
                    print(f"\n💡 產生 Agent 派工 Prompt：\n  uv run master-os document prompt \"{res['filename']}\"")
                    print(f"💡 或直接由本地 Agent 解析更新 DB：\n  uv run master-os document ingest \"{res['filename']}\"")
            elif args.doc_cmd == "ingest":
                try:
                    print(f"🚀 開始 Ingest 文件: {args.filename}")
                    print(f"[1/4] 讀取儲存文件 data/documents/{args.filename}...")
                    res = ingest_document_to_db(repo_root, args.filename, db=db, events=events)
                    print(f"[2/4] PyMuPDF C++ 解析完成：{res['pages']} 頁、{res['chars']} 字 ({res['engine']})")
                    print(f"[3/4] 提取義務與任務：已建立 {res['obligations_created']} 個 Obligations、{res['tasks_created']} 個 Tasks")
                    for ob in res.get("obligations", []):
                        print(f"      + Obligation: {ob['title']} ({ob['id']})")
                    for t in res.get("tasks", []):
                        print(f"      + Task: {t['title']} ({t['id']})")
                    print(f"[4/4] 寫入本地 DB (.master-os/master.db) 並記錄 Agent Run: {res['run_id']}")
                    print("\n✅ Master OS 本地狀態已成功更新！可在 Cockpit (http://127.0.0.1:8765) 查看 Tasks 與 Obligations。")
                except FileNotFoundError as exc:
                    print(f"錯誤: {exc}", file=sys.stderr)
                    sys.exit(1)
            elif args.doc_cmd == "list":
                docs = list_documents(repo_root, db=db)
                if not docs:
                    print("目前沒有儲存的文件或簡報。")
                else:
                    print("==================================================")
                    print("          MASTER OS · DOCUMENTS & PRESENTATIONS   ")
                    print("==================================================")
                    for d in docs:
                        art = f" [{d['artifact_id']}]" if d.get("artifact_id") else ""
                        ext = f" · {d['pages']}頁/{d['chars']}字" if d.get('pages') else ""
                        print(f"• [{d['date']}] {d['filename']} ({d['size_bytes']} bytes){ext}{art}")
            elif args.doc_cmd == "prompt":
                from master_os.documents import generate_document_agent_prompt
                try:
                    prompt = generate_document_agent_prompt(repo_root, args.filename)
                    print(prompt)
                except FileNotFoundError as exc:
                    print(f"錯誤: {exc}", file=sys.stderr)
                    sys.exit(1)

        elif args.command == "dispatch":
            task = db.fetchone("SELECT * FROM tasks WHERE id = ?", (args.task_id,))
            if not task:
                print(f"Task 不存在: {args.task_id}", file=sys.stderr)
                sys.exit(2)
            if task["agentability"] != "autonomous":
                print(f"Task {args.task_id} 未授權 autonomous dispatch。", file=sys.stderr)
                sys.exit(3)

            events = EventStore(db)
            artifacts = ArtifactRegistry(db, repo_root, events=events)
            builder = WorkPacketBuilder(db)
            runtime = AgentRuntime(db, events, artifacts, repo_root)
            workspace = repo_root / ".master-os" / "worktrees" / f"cli-{args.task_id.lower()}"
            packet = builder.build_packet(args.task_id, workspace_path=str(workspace), repo_name=repo_root.name)
            executor = build_local_executors()[task["preferred_agent"]]
            result = runtime.dispatch_autonomous_job(
                packet,
                agent_type=task["preferred_agent"],
                executor_func=executor,
            )
            print(f"Task {args.task_id} → Run {result['run_id']}，狀態: {result['status']}")
            if result.get("error"):
                print(f"錯誤: {result['error']}", file=sys.stderr)
    finally:
        db.close()
