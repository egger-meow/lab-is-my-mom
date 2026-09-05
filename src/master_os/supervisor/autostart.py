"""Cross-platform boot/login autostart for the local Master OS mothership."""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional


CommandRunner = Callable[..., Any]


class AutostartManager:
    """Install/remove a user-scoped login service without embedding credentials."""

    TASK_NAME = "MasterOS"
    SERVICE_NAME = "master-os.service"

    def __init__(
        self,
        repo_root: Path,
        *,
        executable: Optional[Path] = None,
        platform_name: Optional[str] = None,
        home: Optional[Path] = None,
        runner: CommandRunner = subprocess.run,
        port: int = 8000,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.executable = Path(executable or sys.argv[0]).resolve() if executable else Path(sys.argv[0])
        self.platform_name = (platform_name or sys.platform).lower()
        self.home = (home or Path.home()).resolve()
        self.runner = runner
        self.port = int(port)
        if self.port <= 0 or self.port > 65535:
            raise ValueError("port must be between 1 and 65535")

    def _service_command(self) -> str:
        exe = str(self.executable)
        if self.platform_name.startswith("win"):
            return f'"{exe}" start --host 127.0.0.1 --port {self.port}'
        return f'"{exe}" start --host 127.0.0.1 --port {self.port}'

    def plan(self) -> dict[str, Any]:
        if self.platform_name.startswith("win"):
            return {
                "kind": "windows-scheduled-task",
                "task_name": self.TASK_NAME,
                "task_command": self._service_command(),
            }

        if self.platform_name.startswith("linux"):
            service_path = self.home / ".config" / "systemd" / "user" / self.SERVICE_NAME
            working_dir = str(self.repo_root).replace('"', '\\"')
            executable = str(self.executable).replace('"', '\\"')
            content = "\n".join(
                [
                    "[Unit]",
                    "Description=Master OS local mothership",
                    "After=network-online.target",
                    "Wants=network-online.target",
                    "",
                    "[Service]",
                    "Type=simple",
                    f'WorkingDirectory="{working_dir}"',
                    f'ExecStart="{executable}" start --host 127.0.0.1 --port {self.port}',
                    "Restart=on-failure",
                    "RestartSec=5",
                    "",
                    "[Install]",
                    "WantedBy=default.target",
                    "",
                ]
            )
            return {
                "kind": "systemd-user",
                "service_path": str(service_path),
                "content": content,
            }

        raise RuntimeError(f"Unsupported platform for Master OS autostart: {self.platform_name}")

    def install(self) -> dict[str, Any]:
        plan = self.plan()
        if plan["kind"] == "systemd-user":
            service_path = Path(plan["service_path"])
            service_path.parent.mkdir(parents=True, exist_ok=True)
            service_path.write_text(plan["content"], encoding="utf-8")
            self._run(["systemctl", "--user", "daemon-reload"])
            self._run(["systemctl", "--user", "enable", "--now", self.SERVICE_NAME])
            return {**plan, "installed": True}

        task_command = plan["task_command"]
        self._run(
            [
                "schtasks",
                "/Create",
                "/SC",
                "ONLOGON",
                "/TN",
                self.TASK_NAME,
                "/TR",
                task_command,
                "/F",
                "/RL",
                "LIMITED",
            ]
        )
        return {**plan, "installed": True}

    def uninstall(self) -> dict[str, Any]:
        plan = self.plan()
        if plan["kind"] == "systemd-user":
            # Stop/disable best-effort, then remove the unit. A missing service is not
            # a reason to leave a stale file behind.
            self._run(["systemctl", "--user", "disable", "--now", self.SERVICE_NAME], check=False)
            service_path = Path(plan["service_path"])
            if service_path.exists():
                service_path.unlink()
            self._run(["systemctl", "--user", "daemon-reload"])
            return {**plan, "installed": False}

        self._run(["schtasks", "/Delete", "/TN", self.TASK_NAME, "/F"], check=False)
        return {**plan, "installed": False}

    def status(self) -> dict[str, Any]:
        plan = self.plan()
        if plan["kind"] == "systemd-user":
            path = Path(plan["service_path"])
            return {**plan, "installed": path.exists()}
        # Query is intentionally read-only and does not expose environment/secrets.
        try:
            result = self.runner(
                ["schtasks", "/Query", "/TN", self.TASK_NAME],
                capture_output=True,
                text=True,
                check=False,
            )
            installed = getattr(result, "returncode", 1) == 0
        except (FileNotFoundError, OSError):
            installed = False
        return {**plan, "installed": installed}

    def _run(self, command: list[str], *, check: bool = True) -> Any:
        try:
            return self.runner(command, capture_output=True, text=True, check=check)
        except TypeError:
            # Small injectable runners used by tests need not implement subprocess's
            # full keyword surface.
            return self.runner(command)
        except FileNotFoundError as exc:
            raise RuntimeError(f"Autostart command is unavailable: {command[0]}") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(
                f"Autostart command failed ({shlex.join(command)}): {stderr or exc.returncode}"
            ) from exc
