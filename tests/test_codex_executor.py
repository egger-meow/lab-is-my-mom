"""Regression tests for the real local Codex execution boundary."""
from pathlib import Path
import subprocess

import pytest

from master_os.agents.executors import CodexCliExecutor
from master_os.agents.packet import AgentJobPacket


def _packet(workspace: Path) -> AgentJobPacket:
    return AgentJobPacket(
        job_id="JOB-test",
        task_id="T-test",
        objective="Fix the parser",
        why="Required by a confirmed task",
        repo_name="demo",
        branch="agent/test",
        workspace_path=str(workspace),
        permissions={"network": False, "filesystem": "worktree_only"},
        acceptance_criteria=["tests pass"],
        expected_artifacts=[],
    )


def test_codex_executor_refuses_when_cli_is_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("master_os.agents.executors.shutil.which", lambda name: None)
    executor = CodexCliExecutor()
    with pytest.raises(RuntimeError, match="Codex CLI"):
        executor(tmp_path, _packet(tmp_path))


def test_codex_executor_runs_noninteractive_workspace_sandbox_and_records_real_changes(tmp_path: Path, monkeypatch):
    (tmp_path / "existing.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("master_os.agents.executors.shutil.which", lambda name: "/usr/bin/codex")

    commands = []

    def fake_run(command, **kwargs):
        commands.append((command, kwargs))
        if command[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(command, 0, stdout=" M existing.py\n?? created.py\n", stderr="")
        (tmp_path / "existing.py").write_text("x = 2\n", encoding="utf-8")
        (tmp_path / "created.py").write_text("y = 3\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout='{"type":"turn.completed"}\n', stderr="")

    monkeypatch.setattr("master_os.agents.executors.subprocess.run", fake_run)
    result = CodexCliExecutor()(tmp_path, _packet(tmp_path))

    codex_command = commands[0][0]
    assert codex_command[:3] == ["/usr/bin/codex", "--ask-for-approval", "never"]
    assert "exec" in codex_command
    assert "workspace-write" in codex_command
    assert result["exit_code"] == 0
    assert "existing.py" in result["artifacts"]
    assert "created.py" in result["artifacts"]
    assert result["findings"] == []
