"""System Doctor and Diagnostics for Master OS."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from master_os.core.database import MasterDatabase
from master_os.supervisor.backup import BackupManager
from master_os.agents.critic import MasterCritic


class MasterDoctor:
    """Performs comprehensive diagnostics on database, artifacts, resources, and research health."""

    def __init__(self, db: MasterDatabase, repo_root: Path) -> None:
        self.db = db
        self.repo_root = repo_root.resolve()
        self.backup_mgr = BackupManager(db, repo_root)
        self.critic = MasterCritic(db)

    def run_diagnostics(self) -> dict[str, Any]:
        results: dict[str, Any] = {
            "status": "healthy",
            "checks": {},
            "warnings": [],
            "stats": {},
        }

        # 1. Database integrity
        db_health = self.backup_mgr.verify_integrity()
        results["checks"]["database"] = db_health
        if not db_health["integrity_ok"] or db_health["foreign_key_violations"] > 0:
            results["status"] = "degraded"
            results["warnings"].append(f"Database issue: integrity={db_health['integrity_message']}, FK violations={db_health['foreign_key_violations']}")

        # 2. Event store stats
        ev_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM events")["cnt"]
        src_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM sources")["cnt"]
        art_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM artifacts")["cnt"]
        results["stats"] = {
            "total_events": ev_count,
            "total_sources": src_count,
            "total_artifacts": art_count,
        }

        # 3. Worktree check
        worktrees_dir = self.repo_root / ".master-os" / "worktrees"
        orphans = []
        if worktrees_dir.exists():
            orphans = [p.name for p in worktrees_dir.iterdir() if p.is_dir()]
        results["checks"]["active_worktrees"] = orphans

        # 4. Master Health / Research progress
        health = self.critic.evaluate_health()
        results["checks"]["research_health"] = {
            "velocity": health.research_velocity,
            "evidence_count": health.evidence_count,
            "fake_progress_warning": health.fake_progress_warning,
            "message": health.warning_message,
        }
        if health.fake_progress_warning:
            results["warnings"].append(health.warning_message)

        if health.resource_burn_warnings:
            results["warnings"].extend(health.resource_burn_warnings)
            results["status"] = "warning"

        return results
