"""Runtime lifecycle tests for ``master-os start``."""
from pathlib import Path

import pytest

from master_os.cli import run_start
from master_os.core.database import MasterDatabase


def test_run_start_wraps_server_with_supervisor_and_separate_db(tmp_path: Path):
    web_db = MasterDatabase(tmp_path / "master.db")
    calls: list[str] = []
    captured = {}

    class FakeSupervisor:
        def start(self):
            calls.append("supervisor.start")

        def stop(self):
            calls.append("supervisor.stop")

    def supervisor_builder(supervisor_db, repo_root):
        assert supervisor_db is not web_db
        assert supervisor_db.db_path == web_db.db_path
        assert repo_root == tmp_path.resolve()
        captured["supervisor_db"] = supervisor_db
        return FakeSupervisor()

    def app_builder(db, repo_root, agent_executors):
        assert db is web_db
        assert repo_root == tmp_path.resolve()
        assert isinstance(agent_executors, dict)
        return "APP"

    def server_runner(app, *, host, port):
        assert app == "APP"
        assert host == "127.0.0.1"
        assert port == 8000
        calls.append("server")

    try:
        run_start(
            web_db,
            tmp_path,
            host="127.0.0.1",
            port=8000,
            supervisor_builder=supervisor_builder,
            app_builder=app_builder,
            executor_builder=lambda: {},
            server_runner=server_runner,
        )
        assert calls == ["supervisor.start", "server", "supervisor.stop"]
        with pytest.raises(Exception):
            captured["supervisor_db"].execute("SELECT 1")
    finally:
        web_db.close()


def test_run_start_stops_supervisor_when_server_crashes(tmp_path: Path):
    web_db = MasterDatabase(tmp_path / "master.db")
    calls: list[str] = []

    class FakeSupervisor:
        def start(self):
            calls.append("start")

        def stop(self):
            calls.append("stop")

    def server_runner(_app, *, host, port):
        calls.append("server")
        raise RuntimeError("server exploded")

    try:
        with pytest.raises(RuntimeError, match="server exploded"):
            run_start(
                web_db,
                tmp_path,
                host="127.0.0.1",
                port=8000,
                supervisor_builder=lambda *_: FakeSupervisor(),
                app_builder=lambda *_args, **_kwargs: "APP",
                executor_builder=lambda: {},
                server_runner=server_runner,
            )
        assert calls == ["start", "server", "stop"]
    finally:
        web_db.close()
