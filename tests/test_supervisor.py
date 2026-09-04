"""Tests for Master OS Supervisor, Backup, and Doctor."""
from pathlib import Path
import pytest

from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.supervisor.backup import BackupManager
from master_os.supervisor.doctor import MasterDoctor


@pytest.fixture
def sup_setup(tmp_path: Path):
    db_path = tmp_path / "test_sup.db"
    db = MasterDatabase(db_path)
    store = EventStore(db)
    backup_mgr = BackupManager(db, repo_root=tmp_path)
    doctor = MasterDoctor(db, repo_root=tmp_path)
    yield db, store, backup_mgr, doctor
    db.close()


def test_backup_create_snapshot_and_verify(sup_setup, tmp_path: Path):
    db, store, backup_mgr, _ = sup_setup
    source = store.register_source("system", "Test", "test")
    store.record_event("test.event", source.id, {"val": 42})

    snapshot_file = backup_mgr.create_snapshot()
    assert snapshot_file.exists()
    assert snapshot_file.stat().st_size > 0

    integrity = backup_mgr.verify_integrity(snapshot_file)
    assert integrity["integrity_ok"] is True
    assert integrity["foreign_key_violations"] == 0


def test_backup_restore(sup_setup, tmp_path: Path):
    db, store, backup_mgr, _ = sup_setup
    source = store.register_source("system", "Test", "test")
    store.record_event("test.event", source.id, {"val": 100})

    # Snapshot with 1 event
    snapshot_file = backup_mgr.create_snapshot()

    # Add second event to live db
    store.record_event("test.event.2", source.id, {"val": 200})
    cnt_before = db.fetchone("SELECT COUNT(*) as cnt FROM events")["cnt"]
    assert cnt_before == 2

    # Restore from snapshot
    backup_mgr.restore_from_snapshot(snapshot_file)
    cnt_after = db.fetchone("SELECT COUNT(*) as cnt FROM events")["cnt"]
    assert cnt_after == 1


def test_doctor_diagnostics(sup_setup):
    _, _, _, doctor = sup_setup
    diag = doctor.run_diagnostics()

    assert diag["status"] == "healthy"
    assert diag["checks"]["database"]["integrity_ok"] is True
    assert "total_events" in diag["stats"]
    assert "research_health" in diag["checks"]
