"""First-run live bootstrap and readiness checks for Master OS."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping, Optional

from master_os.core.database import MasterDatabase
from master_os.supervisor.autostart import AutostartManager
from master_os.supervisor.backup import BackupManager
from master_os.supervisor.doctor import MasterDoctor


class SetupManager:
    """Prepare a clone for real daily use without storing secrets in the repo.

    The setup flow is intentionally conservative: it creates local runtime
    directories and a verified first backup, checks optional live integrations,
    and may install user-scoped autostart only when explicitly requested.
    """

    def __init__(
        self,
        db: MasterDatabase,
        repo_root: Path,
        *,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.db = db
        self.repo_root = repo_root.resolve()
        self.env: Mapping[str, str] = os.environ if env is None else env
        self.backups = BackupManager(db, self.repo_root)
        self.doctor = MasterDoctor(db, self.repo_root)

    def run(self, *, install_autostart: bool = False, port: int = 8000) -> dict[str, Any]:
        runtime_root = self.repo_root / ".master-os"
        for child in ("agent-packets", "worktrees", "backups"):
            (runtime_root / child).mkdir(parents=True, exist_ok=True)

        checks = {
            "database": self._database_check(),
            "codex": self._command_check("codex", ["--version"]),
            "tailscale": self._command_check("tailscale", ["status", "--json"]),
            "slack": self._slack_check(),
        }

        snapshots = sorted((runtime_root / "backups").glob("master_snapshot_*.db"))
        if snapshots:
            backup = {"status": "existing", "path": str(snapshots[-1])}
        else:
            snapshot = self.backups.create_snapshot()
            integrity = self.backups.verify_integrity(snapshot)
            if not integrity["integrity_ok"] or integrity["foreign_key_violations"]:
                raise RuntimeError(f"Initial backup failed integrity verification: {integrity}")
            backup = {"status": "created", "path": str(snapshot), "integrity": integrity}
        checks["backup"] = backup

        autostart = AutostartManager(self.repo_root, port=port)
        if install_autostart:
            checks["autostart"] = autostart.install()
        else:
            checks["autostart"] = autostart.status()

        doctor = self.doctor.run_diagnostics()
        required_failures = [
            name for name in ("database", "backup")
            if checks[name].get("status") in {"failed", "misconfigured"}
        ]
        optional_warnings = [
            name for name in ("codex", "tailscale", "slack", "autostart")
            if not self._optional_ready(name, checks[name])
        ]
        return {
            "status": "blocked" if required_failures else ("ready_with_warnings" if optional_warnings else "ready"),
            "checks": checks,
            "doctor": doctor,
            "required_failures": required_failures,
            "optional_warnings": optional_warnings,
            "next_commands": self._next_commands(checks, port),
        }

    def _database_check(self) -> dict[str, Any]:
        integrity = self.backups.verify_integrity()
        ok = bool(integrity["integrity_ok"]) and int(integrity["foreign_key_violations"]) == 0
        return {"status": "ready" if ok else "failed", **integrity}

    @staticmethod
    def _command_check(command: str, args: list[str]) -> dict[str, Any]:
        executable = shutil.which(command)
        if not executable:
            return {"status": "missing", "executable": None}
        try:
            completed = subprocess.run(
                [executable, *args],
                capture_output=True,
                text=True,
                check=False,
                timeout=8,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"status": "failed", "executable": executable, "error": str(exc)}
        output = (completed.stdout or completed.stderr or "").strip()
        return {
            "status": "ready" if completed.returncode == 0 else "unavailable",
            "executable": executable,
            "returncode": completed.returncode,
            "output": output[:1200],
        }

    def _slack_check(self) -> dict[str, Any]:
        token = str(self.env.get("SLACK_BOT_TOKEN", "")).strip()
        scopes = str(self.env.get("MASTER_OS_SLACK_CONVERSATIONS", "")).strip()
        if not token and not scopes:
            return {
                "status": "disabled",
                "message": "Slack ingestion is optional until configured.",
            }
        if not token or not scopes:
            return {
                "status": "misconfigured",
                "message": "Set both SLACK_BOT_TOKEN and MASTER_OS_SLACK_CONVERSATIONS.",
            }
        count = len([item for item in scopes.split(",") if item.strip()])
        return {
            "status": "ready",
            "conversation_count": count,
            "message": "Slack credentials are present; token value is never persisted by setup.",
        }

    @staticmethod
    def _optional_ready(name: str, check: dict[str, Any]) -> bool:
        status = check.get("status")
        if name == "slack":
            return status in {"ready", "disabled"}
        if name == "autostart":
            return bool(check.get("installed"))
        return status == "ready"

    @staticmethod
    def _next_commands(checks: dict[str, Any], port: int) -> list[str]:
        commands: list[str] = []
        if checks["codex"].get("status") != "ready":
            commands.append("Install/authenticate Codex CLI, then run: codex --version")
        if checks["tailscale"].get("status") != "ready":
            commands.append("Install/login Tailscale if remote Cockpit access is wanted")
        if checks["slack"].get("status") == "misconfigured":
            commands.append("Fix SLACK_BOT_TOKEN + MASTER_OS_SLACK_CONVERSATIONS together")
        elif checks["slack"].get("status") == "disabled":
            commands.append("Optional: configure scoped Slack ingestion when the bot token/channel IDs are ready")
        if not checks["autostart"].get("installed"):
            commands.append(f"uv run master-os setup --install-autostart --port {port}")
        commands.append(f"uv run master-os start --host 127.0.0.1 --port {port}")
        commands.append("uv run master-os doctor")
        return commands
