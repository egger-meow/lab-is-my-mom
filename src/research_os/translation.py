"""Optional, subprocess-isolated document translation adapters.

The core corpus remains usable without any translation software.  BabelDOC is
kept outside the Python dependency graph because its supported integration
boundary is a command-line invocation and its deployment/license choices are
owned by the caller.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class TranslationUnavailable(RuntimeError):
    """Raised when an optional translator is not locally installed."""


@dataclass(frozen=True)
class TranslationResult:
    command: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str


class Translator(Protocol):
    def translate(self, source_pdf: Path, config_path: Path, *, timeout: int = 3600) -> TranslationResult: ...


class BabelDocTranslator:
    """Run BabelDOC through its documented CLI, never its internal Python API.

    The caller supplies a local TOML file containing the output path, languages,
    and provider credentials.  This adapter neither reads nor persists that
    configuration, preventing credentials from entering corpus provenance.
    """

    def __init__(self, executable: str = "babeldoc") -> None:
        self.executable = executable

    def available(self) -> bool:
        return Path(self.executable).exists() if Path(self.executable).parent != Path(".") else shutil.which(self.executable) is not None

    def translate(self, source_pdf: Path, config_path: Path, *, timeout: int = 3600) -> TranslationResult:
        if not source_pdf.is_file() or source_pdf.suffix.lower() != ".pdf":
            raise ValueError(f"BabelDOC requires an existing PDF: {source_pdf}")
        if not config_path.is_file():
            raise ValueError(f"BabelDOC requires an existing TOML config: {config_path}")
        if not self.available():
            raise TranslationUnavailable(f"BabelDOC executable is unavailable: {self.executable}")
        command = (self.executable, "--config", str(config_path), "--files", str(source_pdf))
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
        return TranslationResult(command, completed.returncode, completed.stdout, completed.stderr)
