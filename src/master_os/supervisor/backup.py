"""Backup and disaster recovery engine for Master OS."""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.reducer import rebuild_state


class BackupManager:
    """Manages atomic SQLite snapshots, backup verification, and disaster recovery."""

    def __init__(self, db: MasterDatabase, repo_root: Path) -> None:
        self.db = db
        self.repo_root = repo_root.resolve()
        self.backup_dir = self.repo_root / "data" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self) -> Path:
        """Create a consistent atomic snapshot of Master DB using SQLite backup API."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"master_snapshot_{timestamp}.db"

        dest_conn = sqlite3.connect(str(backup_file))
        try:
            self.db.conn.backup(dest_conn)
        finally:
            dest_conn.close()

        return backup_file

    def verify_integrity(self, db_path: Optional[Path] = None) -> dict[str, Any]:
        """Verify SQLite integrity and foreign key validity."""
        target = db_path or self.db.db_path
        conn = sqlite3.connect(str(target))
        try:
            integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()
            is_ok = len(integrity_rows) == 1 and integrity_rows[0][0] == "ok"
            fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            return {
                "db_path": str(target),
                "integrity_ok": is_ok,
                "integrity_message": integrity_rows[0][0] if integrity_rows else "failed",
                "foreign_key_violations": len(fk_violations),
            }
        finally:
            conn.close()

    def restore_from_snapshot(self, snapshot_path: Path) -> None:
        """Restore Master DB from an existing snapshot and restore connection policy."""
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        self.db.close()
        shutil.copy2(snapshot_path, self.db.db_path)
        self.db.conn = sqlite3.connect(str(self.db.db_path), check_same_thread=False)
        self.db.conn.row_factory = sqlite3.Row
        self.db.conn.execute("PRAGMA journal_mode = WAL")
        self.db.conn.execute("PRAGMA foreign_keys = ON")
        self.db.conn.execute("PRAGMA busy_timeout = 5000")

    def rebuild_current_state(self) -> int:
        """Rebuild all current state tables deterministically from canonical event history."""
        return rebuild_state(self.db)
