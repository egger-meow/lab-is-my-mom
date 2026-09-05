from pathlib import Path

from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.web.api import create_app


def test_cockpit_html_exposes_interrupted_run_recovery_controls(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        response = TestClient(create_app(db, repo_root=tmp_path)).get("/")
        assert response.status_code == 200
        html = response.text
        assert 'id="interrupted-runs-container"' in html
        assert "recoverInterruptedRun" in html
        assert "繼續原 Worktree" in html
        assert "乾淨重跑" in html
        assert "放棄這次 Run" in html
    finally:
        db.close()
