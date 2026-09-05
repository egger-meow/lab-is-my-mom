"""Durable, non-blocking local agent dispatch queue."""
from __future__ import annotations

import hashlib
import json
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Optional

from master_os.agents.packet import AgentJobPacket, WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id, utc_now
from master_os.core.reducer import apply_event


AgentExecutor = Callable[[Path, AgentJobPacket], dict[str, Any]]


class AgentDispatcher:
    """Persist jobs first, then execute them asynchronously in bounded workers.

    SQLite is the durable queue. A process restart therefore loses only in-memory
    futures, never queued work. Every worker opens its own SQLite connection.
    """

    ACTIVE_STATUSES = ("queued", "running", "recovering")

    def __init__(
        self,
        db: MasterDatabase,
        repo_root: Path,
        executors: Optional[dict[str, AgentExecutor]] = None,
        *,
        max_workers: int = 2,
    ) -> None:
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        self.db = db
        self.repo_root = repo_root.resolve()
        self.executors = dict(executors or {})
        self.max_workers = int(max_workers)
        self.events = EventStore(db)
        self.packet_builder = WorkPacketBuilder(db)
        self.pool = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="master-os-agent")
        self._lock = threading.Lock()
        self._futures: dict[str, Future[Any]] = {}
        self.packet_dir = self.repo_root / ".master-os" / "agent-packets"
        self.packet_dir.mkdir(parents=True, exist_ok=True)
        self.dispatch_source = self.events.register_source(
            "agent_dispatcher", "Agent Dispatcher", "master-os-agent-dispatcher"
        )
        self.artifact_source = self.events.register_source(
            "artifact_registry", "Artifact Registry", "master-os-artifacts"
        )

    def enqueue_task(self, task_id: str) -> dict[str, Any]:
        """Durably queue one autonomous task without requiring an executor to be online."""
        task = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        if task["agentability"] != "autonomous":
            raise RuntimeError(f"Task {task_id} is not authorized for autonomous execution")

        run_id = generate_id("RUN-")
        workspace = self.repo_root / ".master-os" / "worktrees" / f"run-{run_id.lower()}"
        branch = f"agent/{task_id.lower()}-{run_id[-6:].lower()}"
        packet = self.packet_builder.build_packet(
            task_id,
            workspace_path=str(workspace),
            branch=branch,
            repo_name=self.repo_root.name,
        )
        # One durable identity across queue, packet and execution.
        packet.job_id = run_id
        packet_bytes = json.dumps(asdict(packet), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        packet_path = self.packet_dir / f"{run_id}.json"
        rel_packet_path = packet_path.relative_to(self.repo_root).as_posix()
        packet_hash = hashlib.sha256(packet_bytes).hexdigest()
        packet_artifact_id = generate_id("A-")
        now = utc_now()

        try:
            self.db.execute("BEGIN IMMEDIATE")
            active = self.db.fetchone(
                """SELECT id, status FROM agent_runs
                   WHERE task_id = ? AND status IN ('queued', 'running', 'recovering')
                   ORDER BY created_at DESC LIMIT 1""",
                (task_id,),
            )
            if active:
                raise RuntimeError(
                    f"Task {task_id} already has queued/active run {active['id']} ({active['status']}); lease is held"
                )

            packet_path.write_bytes(packet_bytes)
            artifact_event = self.events.record_event(
                "artifact.created",
                self.artifact_source.id,
                {
                    "id": packet_artifact_id,
                    "artifact_type": "agent_packet",
                    "path": rel_packet_path,
                    "content_hash": packet_hash,
                    "canonical": True,
                    "git_sha": AgentRuntime._get_head_sha(self.repo_root),
                    "created_by_agent_run": None,
                    "created_by_experiment": None,
                    "metadata": {"run_id": run_id, "task_id": task_id, "frozen": True},
                    "created_at": now,
                },
                dedup_key=f"agent-packet:{run_id}:{packet_hash}",
                raw_ref=rel_packet_path,
                raw_content=packet_bytes,
                commit=False,
            )
            apply_event(self.db, artifact_event, commit=False)

            queued_event = self.events.record_event(
                "agent_run.queued",
                self.dispatch_source.id,
                {
                    "id": run_id,
                    "agent_type": task["preferred_agent"] or "codex",
                    "job_type": "implementation",
                    "task_id": task_id,
                    "workspace": str(workspace.resolve()),
                    "branch": branch,
                    "base_git_sha": AgentRuntime._get_head_sha(self.repo_root),
                    "packet_artifact_id": packet_artifact_id,
                    "created_at": now,
                },
                dedup_key=f"agent-run-queued:{run_id}",
                commit=False,
            )
            apply_event(self.db, queued_event, commit=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
            # A file without canonical history is only temp debris. Do not leave it
            # looking like a valid frozen packet after a rejected queue claim.
            if packet_path.exists() and self.db.fetchone("SELECT id FROM artifacts WHERE id = ?", (packet_artifact_id,)) is None:
                packet_path.unlink(missing_ok=True)
            raise

        return {
            "run_id": run_id,
            "task_id": task_id,
            "status": "queued",
            "packet_artifact_id": packet_artifact_id,
        }

    def pump_once(self) -> dict[str, Any]:
        """Submit queued work up to capacity and return immediately."""
        with self._lock:
            self._reap_finished_locked()
            capacity = self.max_workers - len(self._futures)
            if capacity <= 0:
                return {"submitted": [], "blocked": [], "inflight": list(self._futures)}

            rows = self.db.fetchall(
                "SELECT * FROM agent_runs WHERE status = 'queued' ORDER BY created_at ASC LIMIT ?",
                (max(capacity * 4, capacity),),
            )
            submitted: list[str] = []
            blocked: list[dict[str, str]] = []
            for row in rows:
                if len(submitted) >= capacity:
                    break
                run_id = row["id"]
                if run_id in self._futures:
                    continue
                agent_type = row["agent_type"] or "codex"
                if agent_type not in self.executors:
                    blocked.append({"run_id": run_id, "reason": f"executor unavailable: {agent_type}"})
                    continue
                future = self.pool.submit(self._execute_queued_run, run_id, agent_type)
                self._futures[run_id] = future
                submitted.append(run_id)

            return {"submitted": submitted, "blocked": blocked, "inflight": list(self._futures)}

    def inflight(self) -> list[str]:
        with self._lock:
            self._reap_finished_locked()
            return list(self._futures)

    def shutdown(self, *, wait: bool = True) -> None:
        self.pool.shutdown(wait=wait, cancel_futures=False)

    def _reap_finished_locked(self) -> None:
        finished = [run_id for run_id, future in self._futures.items() if future.done()]
        for run_id in finished:
            # Calling result consumes the exception so worker failures do not become
            # unobserved Future warnings. The durable run state is authoritative.
            future = self._futures.pop(run_id)
            try:
                future.result()
            except Exception:
                pass

    def _load_packet(self, db: MasterDatabase, run_id: str) -> AgentJobPacket:
        row = db.fetchone(
            """SELECT ar.packet_artifact_id, a.path
               FROM agent_runs ar
               LEFT JOIN artifacts a ON a.id = ar.packet_artifact_id
               WHERE ar.id = ?""",
            (run_id,),
        )
        if not row or not row["packet_artifact_id"] or not row["path"]:
            raise RuntimeError(f"Queued run {run_id} has no frozen work packet artifact")
        path = Path(row["path"])
        actual = path if path.is_absolute() else self.repo_root / path
        payload = json.loads(actual.read_text(encoding="utf-8"))
        return AgentJobPacket(**payload)

    def _execute_queued_run(self, run_id: str, agent_type: str) -> None:
        worker_db = MasterDatabase(self.db.db_path)
        try:
            events = EventStore(worker_db)
            artifacts = ArtifactRegistry(worker_db, self.repo_root, events=events)
            runtime = AgentRuntime(worker_db, events, artifacts, self.repo_root)
            packet = self._load_packet(worker_db, run_id)
            executor = self.executors[agent_type]
            runtime.execute_queued_job(
                run_id,
                packet,
                agent_type=agent_type,
                executor_func=executor,
            )
        finally:
            worker_db.close()
