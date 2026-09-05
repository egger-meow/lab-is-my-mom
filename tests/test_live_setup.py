from pathlib import Path

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
