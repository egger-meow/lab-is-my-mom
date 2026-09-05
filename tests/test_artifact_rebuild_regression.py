from pathlib import Path

from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.reducer import rebuild_state


def test_artifacts_and_version_identity_survive_rebuild(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        registry = ArtifactRegistry(db, repo_root=tmp_path)
        path = tmp_path / "results.csv"
        path.write_text("acc,0.8\n", encoding="utf-8")
        first = registry.register_file(path, "experiment_metrics")

        path.write_text("acc,0.9\n", encoding="utf-8")
        second = registry.register_file(path, "experiment_metrics")
        assert first.id != second.id
        assert registry.get_by_id(first.id).canonical is False
        assert registry.get_by_id(second.id).canonical is True

        rebuild_state(db)

        assert registry.get_by_id(first.id) is not None
        assert registry.get_by_id(first.id).canonical is False
        assert registry.get_by_id(second.id) is not None
        assert registry.get_by_id(second.id).canonical is True
    finally:
        db.close()
