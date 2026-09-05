from pathlib import Path
from types import SimpleNamespace

from master_os.core.database import MasterDatabase
from master_os.supervisor.setup import SetupManager


def test_setup_creates_verified_backup_and_tolerates_optional_tools(tmp_path: Path, monkeypatch):
    db = MasterDatabase(tmp_path / ".master-os" / "master.db")
    monkeypatch.setattr("master_os.supervisor.setup.shutil.which", lambda _name: None)
    try:
        result = SetupManager(db, tmp_path, env={}).run()
    finally:
        db.close()

    assert result["status"] == "ready_with_warnings"
    assert result["checks"]["database"]["status"] == "ready"
    assert result["checks"]["backup"]["status"] == "created"
    assert Path(result["checks"]["backup"]["path"]).exists()
    assert result["checks"]["slack"]["status"] == "disabled"
    assert result["checks"]["codex"]["status"] == "missing"
    assert result["checks"]["tailscale"]["status"] == "missing"
    assert "uv run master-os-setup --install-autostart --port 8000" in result["next_commands"]


def test_setup_flags_half_configured_slack_without_persisting_token(tmp_path: Path, monkeypatch):
    db = MasterDatabase(tmp_path / ".master-os" / "master.db")
    monkeypatch.setattr("master_os.supervisor.setup.shutil.which", lambda _name: None)
    secret = "xoxb-do-not-persist"
    try:
        result = SetupManager(db, tmp_path, env={"SLACK_BOT_TOKEN": secret}).run()
        rows = db.fetchall("SELECT payload_json, raw_ref FROM events")
    finally:
        db.close()

    assert result["checks"]["slack"]["status"] == "misconfigured"
    assert "slack" in result["optional_warnings"]
    serialized = "\n".join(str(dict(row)) for row in rows)
    assert secret not in serialized


def test_command_check_decodes_cli_output_as_utf8(monkeypatch):
    captured = {}
    monkeypatch.setattr("master_os.supervisor.setup.shutil.which", lambda _name: "tailscale.exe")

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout='{"User":"測試使用者"}', stderr="")

    monkeypatch.setattr("master_os.supervisor.setup.subprocess.run", fake_run)

    result = SetupManager._command_check("tailscale", ["status", "--json"])

    assert result["status"] == "ready"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_setup_installs_autostart_with_master_os_executable(tmp_path: Path, monkeypatch):
    db = MasterDatabase(tmp_path / ".master-os" / "master.db")
    seen = {}

    def fake_which(name):
        if name == "master-os":
            return r"C:\\IDEA\\lab-is-my-mom\\.venv\\Scripts\\master-os.exe"
        return None

    class FakeAutostartManager:
        def __init__(self, repo_root, *, executable=None, port=8000, **_kwargs):
            seen["repo_root"] = repo_root
            seen["executable"] = executable
            seen["port"] = port

        def install(self):
            return {"kind": "windows-scheduled-task", "installed": True}

        def status(self):
            return {"kind": "windows-scheduled-task", "installed": False}

    monkeypatch.setattr("master_os.supervisor.setup.shutil.which", fake_which)
    monkeypatch.setattr("master_os.supervisor.setup.AutostartManager", FakeAutostartManager)

    try:
        result = SetupManager(db, tmp_path, env={}).run(install_autostart=True, port=8123)
    finally:
        db.close()

    assert result["checks"]["autostart"]["installed"] is True
    assert seen["executable"] == Path(r"C:\\IDEA\\lab-is-my-mom\\.venv\\Scripts\\master-os.exe")
    assert seen["port"] == 8123
