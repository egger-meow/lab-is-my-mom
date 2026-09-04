"""Artifact Registry for Master OS."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from master_os.core.database import MasterDatabase
from master_os.core.models import Artifact, generate_id, utc_now


class ArtifactRegistry:
    """Passport authority for research files, figures, code, and metrics."""

    def __init__(self, db: MasterDatabase, repo_root: Path) -> None:
        self.db = db
        self.repo_root = repo_root.resolve()

    def relative_path(self, path: Path | str) -> str:
        """Convert path to relative string from repo_root for portability."""
        p = Path(path).resolve()
        try:
            return str(p.relative_to(self.repo_root)).replace("\\", "/")
        except ValueError:
            return str(p).replace("\\", "/")

    def register_file(
        self,
        file_path: Path | str,
        artifact_type: str,
        git_sha: Optional[str] = None,
        created_by_agent_run: Optional[str] = None,
        created_by_experiment: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        content: Optional[bytes] = None,
    ) -> Artifact:
        """Register a file as a tracked research artifact."""
        rel_path = self.relative_path(file_path)
        actual_path = self.repo_root / rel_path

        if content is None:
            if not actual_path.exists():
                raise FileNotFoundError(f"File not found: {actual_path}")
            content = actual_path.read_bytes()

        content_hash = hashlib.sha256(content).hexdigest()

        # Check if identical hash already exists for this path
        existing = self.db.fetchone(
            "SELECT * FROM artifacts WHERE path = ? AND content_hash = ?",
            (rel_path, content_hash)
        )
        if existing:
            return self._row_to_artifact(existing)

        # If previous canonical version existed at this path, mark it non-canonical
        self.db.execute(
            "UPDATE artifacts SET canonical = 0 WHERE path = ? AND canonical = 1",
            (rel_path,)
        )

        aid = generate_id("A-")
        now = utc_now()
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)

        self.db.execute(
            """INSERT INTO artifacts (id, artifact_type, path, content_hash, canonical, git_sha,
                                     created_by_agent_run, created_by_experiment, metadata_json, created_at)
               VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)""",
            (aid, artifact_type, rel_path, content_hash, git_sha, created_by_agent_run, created_by_experiment, meta_json, now)
        )
        self.db.commit()

        return Artifact(
            id=aid,
            artifact_type=artifact_type,
            path=rel_path,
            content_hash=content_hash,
            canonical=True,
            git_sha=git_sha,
            created_by_agent_run=created_by_agent_run,
            created_by_experiment=created_by_experiment,
            metadata=metadata or {},
            created_at=now,
        )

    def get_canonical(self, path: str) -> Optional[Artifact]:
        """Get current canonical artifact for path."""
        rel = path.replace("\\", "/")
        row = self.db.fetchone("SELECT * FROM artifacts WHERE path = ? AND canonical = 1", (rel,))
        return self._row_to_artifact(row) if row else None

    def get_by_id(self, artifact_id: str) -> Optional[Artifact]:
        row = self.db.fetchone("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
        return self._row_to_artifact(row) if row else None

    def _row_to_artifact(self, row: Any) -> Artifact:
        return Artifact(
            id=row["id"],
            artifact_type=row["artifact_type"],
            path=row["path"],
            content_hash=row["content_hash"],
            canonical=bool(row["canonical"]),
            git_sha=row["git_sha"],
            created_by_agent_run=row["created_by_agent_run"],
            created_by_experiment=row["created_by_experiment"],
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
        )
