"""Regression tests for durable asynchronous local agent dispatch."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from master_os.agents.dispatcher import AgentDispatcher
from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore


def _task(db: MasterDatabase, task_id: str = "T-ASYNC") -> None:
    events = EventStore(db)
    source = events.register_source("test", "dispatcher test", "dispatcher-test")
    DomainCommandBus(db, events).emit(
        "task.created",
        source.id,
        {
            "id": task_id,
            "title": "Run asynchronously",
            "agentability": "autonomous",
            "preferred_agent": "codex",
            "acceptance_criteria": ["executor finished"],
        },
        dedup_key=f"task:{task_id}",
    )


def _wait_status(db: MasterDatabase, run_id: str, expected: str, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = db.fetchone("SELECT status FROM agent_runs WHERE id = ?", (run_id,))
        if row and row["status"] == expected:
            return
        time.sleep(0.01)
    row = db.fetchone("SELECT status FROM agent_runs WHERE id = ?", (run_id,))
    raise AssertionError(f"run {run_id} never became {expected}; current={dict(row) if row else None}")


def test_enqueue_is_durable_and_pump_does_not_block_on_long_executor(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    entered = threading.Event()
    release = threading.Event()

    def executor(workspace: Path, _packet):
        entered.set()
        assert release.wait(timeout=5)
        (workspace / "DONE.md").write_text("done", encoding="utf-8")
        return {"exit_code": 0, "artifacts": ["DONE.md"], "findings": []}

    dispatcher = AgentDispatcher(db, tmp_path, {"codex": executor}, max_workers=1)
    try:
        _task(db)
        queued = dispatcher.enqueue_task("T-ASYNC")
        run_id = queued["run_id"]
        assert queued["status"] == "queued"
        row = db.fetchone("SELECT * FROM agent_runs WHERE id = ?", (run_id,))
        assert row["status"] == "queued"
        assert row["packet_artifact_id"] is not None

        start = time.monotonic()
        pumped = dispatcher.pump_once()
        elapsed = time.monotonic() - start
        assert run_id in pumped["submitted"]
        assert elapsed < 0.5
        assert entered.wait(timeout=2)
        _wait_status(db, run_id, "running")

        release.set()
        _wait_status(db, run_id, "completed")
        assert db.fetchone("SELECT status FROM tasks WHERE id='T-ASYNC'")["status"] == "completed"
    finally:
        release.set()
        dispatcher.shutdown(wait=True)
        db.close()


def test_new_dispatcher_after_restart_picks_up_preexisting_queued_run(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        _task(db, "T-RESTART")
        first = AgentDispatcher(db, tmp_path, {}, max_workers=1)
        queued = first.enqueue_task("T-RESTART")
        first.shutdown(wait=True)

        def executor(workspace: Path, _packet):
            (workspace / "RECOVERED.md").write_text("after restart", encoding="utf-8")
            return {"exit_code": 0, "artifacts": ["RECOVERED.md"], "findings": []}

        second = AgentDispatcher(db, tmp_path, {"codex": executor}, max_workers=1)
        try:
            assert queued["run_id"] in second.pump_once()["submitted"]
            _wait_status(db, queued["run_id"], "completed")
        finally:
            second.shutdown(wait=True)
    finally:
        db.close()


def test_same_task_cannot_be_queued_twice(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    dispatcher = AgentDispatcher(db, tmp_path, {}, max_workers=1)
    try:
        _task(db, "T-ONE")
        dispatcher.enqueue_task("T-ONE")
        with pytest.raises(RuntimeError, match="already.*queued|active.*run|lease"):
            dispatcher.enqueue_task("T-ONE")
        assert db.fetchone("SELECT COUNT(*) AS n FROM agent_runs WHERE task_id='T-ONE'")["n"] == 1
    finally:
        dispatcher.shutdown(wait=True)
        db.close()
