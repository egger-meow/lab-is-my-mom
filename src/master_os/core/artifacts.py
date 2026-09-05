"""Artifact Registry for Master OS."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import Artifact, generate_id, utc_now


class ArtifactRegistry:
    """Passport authority for research files, figures, code, and metrics.

    Artifact identity is part of canonical Master OS history. Registering a file
    therefore emits an ``artifact.created`` event and lets the reducer
    materialize the registry. This keeps version history rebuildable.
    """

    def __init__(self, db: MasterDatabase, repo_root: Path, events: Optional[EventStore] = None) -> None:
        self.db = db
        self.repo_root = repo_root.resolve()
        self.events = events or EventStore(db)
        self.commands = DomainCommandBus(db, self.events)

    def relative_path(self, path: Path | str) -> str:
        """Convert path to a portable relative string when it lives under repo_root."""
        p = Path(path).resolve()
        try:
            return p.relative_to(self.repo_root).as_posix()
        except ValueError:
            return p.as_posix()

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
        """Register a file as an immutable, event-backed research artifact."""
        rel_path = self.relative_path(file_path)
        path_obj = Path(file_path)
        actual_path = path_obj if path_obj.is_absolute() else self.repo_root / path_obj

        if content is None:
            if not actual_path.exists():
                raise FileNotFoundError(f"File not found: {actual_path}")
            content = actual_path.read_bytes()

        content_hash = hashlib.sha256(content).hexdigest()

        existing = self.db.fetchone(
            "SELECT * FROM artifacts WHERE path = ? AND content_hash = ? ORDER BY created_at DESC LIMIT 1",
            (rel_path, content_hash),
        )
        if existing:
            return self._row_to_artifact(existing)

        aid = generate_id("A-")
        now = utc_now()
        source = self.events.register_source("artifact_registry", "Artifact Registry", "master-os-artifacts")
        event = self.commands.emit(
            event_type="artifact.created",
            source_id=source.id,
            payload={
                "id": aid,
                "artifact_type": artifact_type,
                "path": rel_path,
                "content_hash": content_hash,
                "canonical": True,
                "git_sha": git_sha,
                "created_by_agent_run": created_by_agent_run,
                "created_by_experiment": created_by_experiment,
                "metadata": metadata or {},
                "created_at": now,
            },
            dedup_key=f"artifact:{rel_path}:{content_hash}",
            raw_ref=rel_path,
            raw_content=content,
        )

        row = self.db.fetchone("SELECT * FROM artifacts WHERE id = ?", (aid,))
        if not row:
            # A deduplicated event may point to a pre-existing artifact id.
            row = self.db.fetchone(
                "SELECT * FROM artifacts WHERE path = ? AND content_hash = ? ORDER BY created_at DESC LIMIT 1",
                (rel_path, content_hash),
            )
        if not row:
            raise RuntimeError(f"Artifact event {event.id} did not materialize {rel_path}")
        return self._row_to_artifact(row)

    def get_canonical(self, path: str) -> Optional[Artifact]:
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
