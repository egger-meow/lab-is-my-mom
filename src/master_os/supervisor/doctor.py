"""System Doctor and Diagnostics for Master OS."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from master_os.agents.critic import MasterCritic
from master_os.core.database import MasterDatabase
from master_os.supervisor.backup import BackupManager


class MasterDoctor:
    """Comprehensive local diagnostics for the two-year Master OS runtime."""

    def __init__(self, db: MasterDatabase, repo_root: Path) -> None:
        self.db = db
        self.repo_root = repo_root.resolve()
        self.backup_mgr = BackupManager(db, repo_root)
        self.critic = MasterCritic(db)

    def _warn(self, results: dict[str, Any], message: str, *, degraded: bool = False) -> None:
        results["warnings"].append(message)
        if degraded:
            results["status"] = "degraded"
        elif results["status"] == "healthy":
            results["status"] = "warning"

    def run_diagnostics(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        results: dict[str, Any] = {
            "status": "healthy",
            "checked_at": now.isoformat(),
            "checks": {},
            "warnings": [],
            "stats": {},
        }

        db_health = self.backup_mgr.verify_integrity()
        results["checks"]["database"] = db_health
        if not db_health["integrity_ok"] or db_health["foreign_key_violations"] > 0:
            self._warn(
                results,
                f"Database issue: integrity={db_health['integrity_message']}, FK violations={db_health['foreign_key_violations']}",
                degraded=True,
            )

        ev_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM events")["cnt"]
        src_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM sources")["cnt"]
        art_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM artifacts")["cnt"]
        queue_counts = {
            row["status"]: row["cnt"]
            for row in self.db.fetchall(
                "SELECT status, COUNT(*) AS cnt FROM agent_runs GROUP BY status"
            )
        }
        results["stats"] = {
            "total_events": ev_count,
            "total_sources": src_count,
            "total_artifacts": art_count,
            "agent_runs_by_status": queue_counts,
        }

        worktrees_dir = self.repo_root / ".master-os" / "worktrees"
        worktrees = []
        if worktrees_dir.exists():
            worktrees = sorted(p.name for p in worktrees_dir.iterdir() if p.is_dir())
        results["checks"]["worktrees"] = worktrees

        snapshots = sorted(
            self.backup_mgr.backup_dir.glob("master_snapshot_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if snapshots:
            latest = snapshots[0]
            age_hours = max(0.0, (now.timestamp() - latest.stat().st_mtime) / 3600.0)
            backup_check = self.backup_mgr.verify_integrity(latest)
            backup_check.update(
                {
                    "latest": str(latest),
                    "age_hours": round(age_hours, 2),
                    "snapshot_count": len(snapshots),
                }
            )
            results["checks"]["backup"] = backup_check
            if not backup_check["integrity_ok"] or backup_check["foreign_key_violations"]:
                self._warn(results, "Latest Master DB backup failed integrity verification", degraded=True)
            elif age_hours > 36:
                self._warn(results, f"Latest Master DB backup is stale ({age_hours:.1f}h old)")
        else:
            # A brand-new install is allowed to be healthy before the first supervisor
            # tick. Production supervisor maintenance creates and verifies the initial
            # snapshot immediately, then keeps it fresh daily.
            results["checks"]["backup"] = {
                "latest": None,
                "snapshot_count": 0,
                "status": "awaiting_first_supervisor_tick",
            }

        supervisor_row = self.db.fetchone(
            "SELECT status, last_heartbeat, message, details_json FROM system_health WHERE subsystem='supervisor'"
        )
        if supervisor_row:
            supervisor = dict(supervisor_row)
            try:
                heartbeat = datetime.fromisoformat(supervisor["last_heartbeat"].replace("Z", "+00:00"))
                if heartbeat.tzinfo is None:
                    heartbeat = heartbeat.replace(tzinfo=timezone.utc)
                age_seconds = max(0.0, (now - heartbeat.astimezone(timezone.utc)).total_seconds())
            except Exception:
                age_seconds = float("inf")
            supervisor["age_seconds"] = None if age_seconds == float("inf") else int(age_seconds)
            results["checks"]["supervisor"] = supervisor
            if age_seconds > 10 * 60:
                self._warn(results, "Supervisor heartbeat is stale; collectors/scheduler/agent queue may not be running")
        else:
            results["checks"]["supervisor"] = {"status": "not_seen", "last_heartbeat": None}

        missing_artifacts: list[str] = []
        for row in self.db.fetchall("SELECT path FROM artifacts WHERE canonical = 1"):
            path = Path(row["path"])
            actual = path if path.is_absolute() else self.repo_root / path
            if not actual.exists():
                missing_artifacts.append(row["path"])
                if len(missing_artifacts) >= 20:
                    break
        results["checks"]["missing_canonical_artifacts"] = missing_artifacts
        if missing_artifacts:
            self._warn(results, f"{len(missing_artifacts)} canonical artifact(s) are missing on disk")

        health = self.critic.evaluate_health()
        results["checks"]["research_health"] = {
            "velocity": health.research_velocity,
            "evidence_count": health.evidence_count,
            "fake_progress_warning": health.fake_progress_warning,
            "message": health.warning_message,
        }
        if health.fake_progress_warning:
            self._warn(results, health.warning_message)
        for warning in health.resource_burn_warnings:
            self._warn(results, warning)

        return results
