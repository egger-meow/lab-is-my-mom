from __future__ import annotations

from pathlib import Path

import pytest

import master_os.cli as cli


@pytest.mark.parametrize("action", ["install", "status", "uninstall"])
def test_cli_routes_autostart_actions_without_starting_server(tmp_path: Path, monkeypatch, capsys, action: str):
    calls: list[str] = []

    class FakeAutostartManager:
        def __init__(self, repo_root: Path, **_kwargs):
            assert repo_root == tmp_path

        def install(self):
            calls.append("install")
            return {"kind": "fake", "installed": True}

        def status(self):
            calls.append("status")
            return {"kind": "fake", "installed": True}

        def uninstall(self):
            calls.append("uninstall")
            return {"kind": "fake", "installed": False}

    monkeypatch.setattr(cli, "get_paths", lambda: (tmp_path, tmp_path / "master.db"))
    monkeypatch.setattr(cli, "AutostartManager", FakeAutostartManager, raising=False)
    monkeypatch.setattr(cli.sys, "argv", ["master-os", "autostart", action])

    cli.main()

    assert calls == [action]
    output = capsys.readouterr().out
    assert "autostart" in output.lower() or "自動啟動" in output
