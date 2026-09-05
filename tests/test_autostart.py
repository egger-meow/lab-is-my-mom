"""Regression tests for Master OS boot/login autostart."""
from __future__ import annotations

from pathlib import Path

import pytest

from master_os.supervisor.autostart import AutostartManager


def test_linux_systemd_unit_restarts_master_os_and_stays_loopback(tmp_path: Path):
    manager = AutostartManager(
        repo_root=tmp_path / "repo with spaces",
        executable=Path("/opt/master os/bin/master-os"),
        platform_name="linux",
        home=tmp_path / "home",
        runner=lambda *_args, **_kwargs: None,
    )

    plan = manager.plan()

    assert plan["kind"] == "systemd-user"
    assert plan["service_path"].endswith(".config/systemd/user/master-os.service")
    unit = plan["content"]
    assert "Restart=on-failure" in unit
    assert "RestartSec=5" in unit
    assert "--host 127.0.0.1" in unit
    assert "--port 8000" in unit
    assert 'WorkingDirectory="' in unit
    assert 'ExecStart="/opt/master os/bin/master-os" start --host 127.0.0.1 --port 8000' in unit


def test_windows_plan_uses_per_user_startup_folder_without_embedding_secrets(tmp_path: Path):
    manager = AutostartManager(
        repo_root=tmp_path / "repo",
        executable=Path(r"C:\Users\me\venv\Scripts\master-os.exe"),
        platform_name="win32",
        home=tmp_path / "home",
        runner=lambda *_args, **_kwargs: None,
    )

    plan = manager.plan()

    assert plan["kind"] == "windows-startup-folder"
    assert plan["startup_path"].endswith("Startup/master-os.cmd")
    command = plan["task_command"]
    assert '"C:\\Users\\me\\venv\\Scripts\\master-os.exe" start --host 127.0.0.1 --port 8000' == command
    assert "SLACK_BOT_TOKEN" not in plan["content"]
    assert "OPENAI_API_KEY" not in plan["content"]
    assert "cd /d" in plan["content"]
    assert "start \"\" /min" in plan["content"]


def test_windows_install_and_uninstall_use_startup_folder_without_shell_commands(tmp_path: Path):
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs):
        calls.append(command)
        return None

    manager = AutostartManager(
        repo_root=tmp_path / "repo",
        executable=Path(r"C:\Users\me\venv\Scripts\master-os.exe"),
        platform_name="win32",
        home=tmp_path / "home",
        runner=runner,
    )

    installed = manager.install()
    startup_path = Path(installed["startup_path"])
    assert installed["installed"] is True
    assert startup_path.exists()
    assert manager.status()["installed"] is True
    assert calls == []

    removed = manager.uninstall()
    assert removed["installed"] is False
    assert not startup_path.exists()
    assert calls == []


def test_linux_install_writes_unit_and_enables_user_service(tmp_path: Path):
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs):
        calls.append(command)
        return None

    manager = AutostartManager(
        repo_root=tmp_path / "repo",
        executable=Path("/usr/local/bin/master-os"),
        platform_name="linux",
        home=tmp_path / "home",
        runner=runner,
    )

    result = manager.install()
    service = tmp_path / "home" / ".config" / "systemd" / "user" / "master-os.service"
    assert service.exists()
    assert result["installed"] is True
    assert calls == [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", "master-os.service"],
    ]


def test_unknown_platform_refuses_to_guess(tmp_path: Path):
    manager = AutostartManager(
        repo_root=tmp_path,
        executable=Path("master-os"),
        platform_name="plan9",
        home=tmp_path,
        runner=lambda *_args, **_kwargs: None,
    )
    with pytest.raises(RuntimeError, match="Unsupported.*autostart"):
        manager.plan()
