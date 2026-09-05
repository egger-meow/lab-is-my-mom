"""Concrete local agent executors.

Executors are deliberately thin adapters. Master OS owns memory, permissions,
worktree isolation, acceptance validation, and provenance; Codex only performs
one bounded job inside the supplied workspace.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from master_os.agents.packet import AgentJobPacket


class CodexCliExecutor:
    """Run OpenAI Codex CLI non-interactively inside an isolated worktree.

    The adapter uses Codex's workspace-write sandbox and never elevates to
    danger-full-access. Network remains disabled unless the work packet
    explicitly grants read-network capability.
    """

    def __init__(self, executable: str = "codex", timeout_seconds: int = 60 * 60) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def __call__(self, workspace: Path, packet: AgentJobPacket) -> dict[str, Any]:
        codex = shutil.which(self.executable)
        if not codex:
            raise RuntimeError(
                "Codex CLI is not installed or not on PATH. Install/authenticate @openai/codex before autonomous dispatch."
            )

        workspace = workspace.resolve()
        prompt = self._build_prompt(packet)
        command = [
            codex,
            "--ask-for-approval",
            "never",
            "exec",
            "--sandbox",
            "workspace-write",
            "--json",
            "--ephemeral",
            "-C",
            str(workspace),
        ]
        if packet.permissions.get("network") is True:
            command.extend(["-c", "sandbox_workspace_write.network_access=true"])
        command.append("-")

        completed = subprocess.run(
            command,
            cwd=workspace,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        log_dir = workspace / ".master-os-agent"
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = log_dir / "codex.jsonl"
        stderr_path = log_dir / "codex.stderr.log"
        stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        stderr_path.write_text(completed.stderr or "", encoding="utf-8")

        changed = self._changed_files(workspace)
        # Wrapper logs are real run artifacts as well, but never research findings.
        artifacts = changed + [
            stdout_path.relative_to(workspace).as_posix(),
            stderr_path.relative_to(workspace).as_posix(),
        ]

        return {
            "exit_code": completed.returncode,
            "artifacts": list(dict.fromkeys(artifacts)),
            "findings": [],
        }

    @staticmethod
    def _build_prompt(packet: AgentJobPacket) -> str:
        payload = {
            "job_id": packet.job_id,
            "task_id": packet.task_id,
            "objective": packet.objective,
            "why": packet.why,
            "repo": packet.repo_name,
            "permissions": packet.permissions,
            "acceptance_criteria": packet.acceptance_criteria,
            "expected_artifacts": packet.expected_artifacts,
            "known_failures": packet.known_failures,
            "context_notes": packet.context_notes,
        }
        return (
            "You are an execution worker for Master OS. Complete exactly this bounded task in the current worktree.\n"
            "Do not merge, push, send messages, spend paid compute, or operate outside the worktree.\n"
            "Do not invent experimental results or claim acceptance criteria passed unless you actually verified them.\n"
            "Preserve existing project instructions and run appropriate local checks.\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )

    @staticmethod
    def _changed_files(workspace: Path) -> list[str]:
        """Return existing changed/untracked paths produced in this worktree."""
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        if status.returncode != 0:
            return []

        paths: list[str] = []
        for line in status.stdout.splitlines():
            if len(line) < 4:
                continue
            raw = line[3:].strip()
            if " -> " in raw:
                raw = raw.split(" -> ", 1)[1]
            raw = raw.strip('"')
            candidate = workspace / raw
            if candidate.is_file():
                paths.append(Path(raw).as_posix())
        return paths


def build_local_executors() -> dict[str, Any]:
    """Return concrete executors that can be injected into the runtime/API."""
    return {"codex": CodexCliExecutor()}
