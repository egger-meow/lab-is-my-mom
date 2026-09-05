"""Regression tests for long-running agent lease safety."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from master_os.agents.packet import WorkPacketBuilder
from master_os.agents.runtime import AgentRuntime
from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.reducer import apply_event


def _create_task(db: MasterDatabase, task_id: str = "T-LEASE") -> None:
    events = EventStore(db)
    source = events.register_source("test", "Agent lease test", "agent-lease-test")
    event = events.record_event(
        "task.created",
        source.id,
        {
            "id": task_id,
            "title": "Run one exclusive agent job",
            "agentability": "autonomous",
            "preferred_agent": "codex",
            "acceptance_criteria": [],
        },
    )
    apply_event(db, event)


def _runtime(db: MasterDatabase, repo_root: Path) -> AgentRuntime:
    events = EventStore(db)
    artifacts = ArtifactRegistry(db, repo_root, events=events)
    return AgentRuntime(db, events, artifacts, repo_root)


def test_second_dispatch_for_same_task_is_rejected_while_first_run_is_active(tmp_path: Path):
    """Two processes/connections must not own the same task at the same time."""
    db_path = tmp_path / "master.db"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    db1 = MasterDatabase(db_path)
    _create_task(db1)
    db2 = MasterDatabase(db_path)

    entered = threading.Event()
    release = threading.Event()
    first_errors: list[BaseException] = []

    try:
        runtime1 = _runtime(db1, repo_root)
        runtime2 = _runtime(db2, repo_root)
        packet1 = WorkPacketBuilder(db1).build_packet(
            "T-LEASE",
            workspace_path=str(repo_root / ".master-os" / "worktrees" / "lease-a"),
            branch="agent/t-lease-a",
        )
        packet2 = WorkPacketBuilder(db2).build_packet(
            "T-LEASE",
            workspace_path=str(repo_root / ".master-os" / "worktrees" / "lease-b"),
            branch="agent/t-lease-b",
        )

        def slow_executor(_workspace: Path, _packet):
            entered.set()
            assert release.wait(timeout=5), "test did not release the first executor"
            return {"exit_code": 0, "artifacts": [], "findings": []}

        def run_first() -> None:
            try:
                runtime1.dispatch_autonomous_job(packet1, executor_func=slow_executor)
            except BaseException as exc:  # surfaced below after releasing the worker
                first_errors.append(exc)

        thread = threading.Thread(target=run_first, daemon=True)
        thread.start()
        assert entered.wait(timeout=5), "first agent run never entered its executor"

        with pytest.raises(RuntimeError, match="already.*active|active.*run|lease"):
            runtime2.dispatch_autonomous_job(
                packet2,
                executor_func=lambda _workspace, _packet: {
                    "exit_code": 0,
                    "artifacts": [],
                    "findings": [],
                },
            )

        release.set()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert first_errors == []
    finally:
        release.set()
        db2.close()
        db1.close()
