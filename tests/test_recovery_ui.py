from pathlib import Path

from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.web.api import create_app


def test_agents_workspace_exposes_interrupted_run_recovery_controls(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        client = TestClient(create_app(db, repo_root=tmp_path))
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert 'id="agents-interrupted"' in html
        assert "中斷待處理" in html

        script = client.get("/static/app.js")
        assert script.status_code == 200
        js = script.text
        assert "recoverRun" in js
        assert "Resume 原 worktree" in js
        assert "乾淨重跑" in js
        assert "放棄 run" in js
    finally:
        db.close()
