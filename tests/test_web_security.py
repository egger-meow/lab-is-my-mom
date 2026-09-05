from pathlib import Path

from fastapi.testclient import TestClient

from master_os.core.database import MasterDatabase
from master_os.web.api import create_app


def test_cockpit_does_not_enable_cross_origin_mutation_by_default(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        client = TestClient(create_app(db, repo_root=tmp_path))
        response = client.options(
            "/api/meetings/ingest",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in response.headers
    finally:
        db.close()
