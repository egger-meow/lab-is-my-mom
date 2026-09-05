"""CLI entrypoint for first-run Master OS setup."""
from __future__ import annotations

import argparse
from pathlib import Path

from master_os.core.database import MasterDatabase
from master_os.supervisor.setup import SetupManager


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="master-os-setup",
        description="Prepare Master OS for real daily use and report live-integration readiness.",
    )
    parser.add_argument("--install-autostart", action="store_true", help="Install user-scoped login autostart")
    parser.add_argument("--port", type=int, default=8000, help="Cockpit port (default: 8000)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    db = MasterDatabase(repo_root / ".master-os" / "master.db")
    try:
        result = SetupManager(db, repo_root).run(
            install_autostart=args.install_autostart,
            port=args.port,
        )
    finally:
        db.close()

    print("==================================================")
    print("             MASTER OS LIVE BOOTSTRAP             ")
    print("==================================================")
    print(f"狀態: {result['status']}")
    for name, check in result["checks"].items():
        state = check.get("status")
        if name == "autostart":
            state = "ready" if check.get("installed") else "not-installed"
        print(f"• {name}: {state}")

    if result["required_failures"]:
        print("\n必要修復：")
        for name in result["required_failures"]:
            print(f"• {name}")

    if result["optional_warnings"]:
        print("\n尚未啟用 / 可選能力：")
        for name in result["optional_warnings"]:
            print(f"• {name}")

    print("\n下一步：")
    for command in result["next_commands"]:
        print(f"• {command}")
