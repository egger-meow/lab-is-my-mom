"""Meeting Agent: evidence ingestion, semantic proposals, meeting packs, Slack drafts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from master_os.core.artifacts import ArtifactRegistry
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import generate_id, utc_now
from master_os.core.reducer import apply_event
from master_os.core.relations import RelationGraph
from master_os.lab.protocol import MEETING_FORMAT, generate_post_meeting_slack_draft


class MeetingAgent:
    """Handle advisor-meeting evidence without turning heuristics into research truth."""

    def __init__(
        self,
        db: MasterDatabase,
        events: EventStore,
        artifacts: ArtifactRegistry,
        relations: RelationGraph,
        repo_root: Path,
    ) -> None:
        self.db = db
        self.events = events
        self.artifacts = artifacts
        self.relations = relations
        self.repo_root = repo_root.resolve()

    def ingest_transcript(
        self,
        meeting_id: str,
        transcript_text: str,
        raw_file_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Persist transcript evidence and queue high-impact semantics for review.

        Heuristic extraction may propose decisions/obligations/tasks, but it never
        materializes Tier-2 research truth by itself.
        """
        source = self.events.register_source(
            "manual_upload", "Meeting Transcript", raw_file_name or f"meeting-{meeting_id}.txt"
        )

        existing = self.db.fetchone("SELECT id FROM meetings WHERE id = ?", (meeting_id,))
        if not existing:
            scheduled = self.events.record_event(
                event_type="meeting.scheduled",
                source_id=source.id,
                payload={
                    "id": meeting_id,
                    "title": f"Advisor Meeting {meeting_id}",
                    "scheduled_at": utc_now(),
                    "kind": "advisor",
                },
                dedup_key=f"meeting:{meeting_id}:created-from-transcript",
            )
            apply_event(self.db, scheduled)

        data_dir = self.repo_root / "data" / "transcripts"
        data_dir.mkdir(parents=True, exist_ok=True)
        file_path = data_dir / f"{meeting_id}.txt"
        file_path.write_text(transcript_text, encoding="utf-8")
        transcript_art = self.artifacts.register_file(
            file_path=file_path,
            artifact_type="transcript",
            metadata={"meeting_id": meeting_id},
        )

        import_event = self.events.record_event(
            event_type="meeting.transcript.imported",
            source_id=source.id,
            payload={"meeting_id": meeting_id, "artifact_id": transcript_art.id},
            raw_content=transcript_text,
            raw_ref=transcript_art.path,
            dedup_key=f"meeting-transcript:{meeting_id}:{transcript_art.content_hash}",
        )

        extracted = self._extract_semantics(transcript_text)
        approval_ids = self._queue_semantic_approvals(meeting_id, extracted, import_event.id)

        completed = self.events.record_event(
            event_type="meeting.completed",
            source_id=source.id,
            payload={"id": meeting_id, "transcript_artifact_id": transcript_art.id},
            dedup_key=f"meeting:{meeting_id}:completed:{transcript_art.content_hash}",
        )
        apply_event(self.db, completed)

        return {
            "transcript_artifact_id": transcript_art.id,
            "transcript_event_id": import_event.id,
            "extracted": extracted,
            "semantic_approval_ids": approval_ids,
        }

    def _queue_semantic_approvals(
        self,
        meeting_id: str,
        extracted: dict[str, Any],
        source_event_id: str,
    ) -> list[str]:
        approval_ids: list[str] = []
        source = self.events.register_source("meeting_agent", "Meeting Semantic Review", "meeting-semantic-review")

        for change_type, key in (
            ("decision", "decisions"),
            ("obligation", "obligations"),
            ("task", "tasks"),
        ):
            for candidate in extracted[key]:
                approval_id = generate_id("AP-")
                event = self.events.record_event(
                    event_type="approval.requested",
                    source_id=source.id,
                    payload={
                        "id": approval_id,
                        "action_type": "confirm_semantic_change",
                        "action_payload": {
                            "change_type": change_type,
                            "meeting_id": meeting_id,
                            "source_event_id": source_event_id,
                            "candidate": candidate,
                        },
                        "reason": "Meeting transcript contains a high-impact semantic candidate that requires confirmation.",
                        "risk_level": "high" if change_type in {"decision", "obligation"} else "medium",
                        "estimated_cost": 0.0,
                    },
                    dedup_key=(
                        f"semantic:{meeting_id}:{source_event_id}:{change_type}:"
                        f"{candidate.get('evidence', candidate.get('statement', candidate.get('title', '')))}"
                    ),
                )
                apply_event(self.db, event)
                approval_ids.append(event.payload["id"])

        return approval_ids

    def apply_semantic_approval(self, approval_id: str) -> Optional[str]:
        """Materialize an approved meeting-semantic candidate exactly once."""
        approval = self.db.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
        if not approval or approval["status"] != "approved" or approval["action_type"] != "confirm_semantic_change":
            return None

        existing = self.relations.get_out_relations("approval", approval_id, "materialized_as")
        if existing:
            return existing[0].to_id

        payload = json.loads(approval["action_payload_json"])
        candidate = payload["candidate"]
        change_type = payload["change_type"]
        meeting_id = payload["meeting_id"]
        source_event_id = payload.get("source_event_id")
        source = self.events.register_source("user", "Confirmed Meeting Semantics", "meeting-semantic-confirmation")

        if change_type == "decision":
            entity_id = generate_id("D-")
            event = self.events.record_event(
                "decision.recorded",
                source.id,
                {
                    "id": entity_id,
                    "statement": candidate["statement"],
                    "rationale": candidate.get("rationale", "Confirmed from meeting evidence"),
                    "status": "active",
                },
                created_by="user_explicit",
            )
            apply_event(self.db, event)
            self.relations.link("decision", entity_id, "decided_in", "meeting", meeting_id, source_event_id=source_event_id)

        elif change_type == "obligation":
            entity_id = generate_id("O-")
            event = self.events.record_event(
                "obligation.created",
                source.id,
                {
                    "id": entity_id,
                    "title": candidate["title"],
                    "description": candidate.get("description", ""),
                    "severity": candidate.get("severity", "high"),
                    "meeting_id": meeting_id,
                    "source_event_id": source_event_id,
                    "satisfaction_rules": [],
                },
                created_by="user_explicit",
            )
            apply_event(self.db, event)
            self.relations.link("meeting", meeting_id, "created", "obligation", entity_id, source_event_id=source_event_id)

        elif change_type == "task":
            entity_id = generate_id("T-")
            event = self.events.record_event(
                "task.created",
                source.id,
                {
                    "id": entity_id,
                    "title": candidate["title"],
                    "description": candidate.get("description", ""),
                    "priority": candidate.get("priority", "high"),
                    "agentability": candidate.get("agentability", "interactive"),
                    "preferred_agent": candidate.get("preferred_agent", "codex"),
                    "acceptance_criteria": [],
                },
                created_by="user_explicit",
            )
            apply_event(self.db, event)
            self.relations.link("task", entity_id, "discussed_in", "meeting", meeting_id, source_event_id=source_event_id)
        else:
            return None

        self.relations.link("approval", approval_id, "materialized_as", change_type, entity_id, source_event_id=source_event_id)
        return entity_id

    def generate_meeting_pack(self, next_meeting_id: str) -> str:
        """Build a source-backed meeting outline without inventing metrics or results."""
        findings = self.db.fetchall(
            "SELECT * FROM findings WHERE status IN ('validated', 'candidate') ORDER BY created_at DESC LIMIT 8"
        )
        obligations = self.db.fetchall(
            "SELECT * FROM obligations WHERE status IN ('pending', 'in_progress') ORDER BY due_at ASC, created_at DESC"
        )
        tasks = self.db.fetchall(
            "SELECT * FROM tasks WHERE status IN ('todo', 'in_progress', 'blocked') ORDER BY created_at DESC LIMIT 10"
        )
        experiments = self.db.fetchall(
            "SELECT * FROM experiments ORDER BY created_at DESC LIMIT 6"
        )

        lines = [
            "# 個人 Meeting 報告簡報大綱 (Meeting Pack)",
            f"**會議 ID**: {next_meeting_id}",
            "",
            f"## 第一階段：進度與承諾回顧 ({MEETING_FORMAT.step1_review})",
        ]
        if obligations:
            for ob in obligations:
                due = f" · due {ob['due_at']}" if ob["due_at"] else ""
                lines.append(f"- [{ob['status']}] **{ob['id']}** {ob['title']}{due}")
        else:
            lines.append("- 目前沒有已確認、待滿足的 Obligation。")

        lines.extend(["", f"## 第二階段：今日討論事項 ({MEETING_FORMAT.step2_agenda})"])
        if tasks:
            for task in tasks[:5]:
                lines.append(f"- **{task['id']}** {task['title']} ({task['status']})")
        else:
            lines.append("- 確認本週研究進度與下一步。")

        lines.extend([
            "",
            f"## 第三階段：實驗進度與 Findings 報告 ({MEETING_FORMAT.step3_discussion})",
            f"> {MEETING_FORMAT.table_guideline}",
            "",
            "### 最近實驗",
            "| ID | 實驗 | 執行狀態 | 證據有效性 | Git SHA |",
            "| --- | --- | --- | --- | --- |",
        ])
        if experiments:
            for exp in experiments:
                lines.append(
                    f"| {exp['id']} | {exp['title']} | {exp['status']} | {exp['validity_status']} | {exp['git_sha'] or '-'} |"
                )
        else:
            lines.append("| - | 尚無已登錄實驗 | - | - | - |")

        lines.extend(["", "### Findings"])
        if findings:
            for finding in findings:
                lines.append(
                    f"- **{finding['id']}** [{finding['status']}] {finding['statement']} "
                    f"(confidence {finding['confidence']:.2f})"
                )
        else:
            lines.append("- 尚無可引用 Finding。不要以缺省值或示範數字填補。")

        pack_text = "\n".join(lines)
        pack_dir = self.repo_root / "data" / "meeting_packs"
        pack_dir.mkdir(parents=True, exist_ok=True)
        pack_file = pack_dir / f"{next_meeting_id}_pack.md"
        pack_file.write_text(pack_text, encoding="utf-8")
        self.artifacts.register_file(
            file_path=pack_file,
            artifact_type="meeting_pack",
            metadata={"meeting_id": next_meeting_id},
        )
        return pack_text

    def create_post_meeting_slack_approval(
        self,
        meeting_id: str,
        meeting_title: str,
        date_str: str,
        discussion_points: list[str],
        next_commitments: list[str],
    ) -> str:
        """Generate a caller-supplied Slack draft and gate external send behind approval."""
        draft = generate_post_meeting_slack_draft(meeting_title, date_str, discussion_points, next_commitments)
        return self._create_slack_approval(meeting_id, draft)

    def create_post_meeting_slack_approval_from_evidence(self, meeting_id: str) -> str:
        """Create one post-meeting Slack draft from preserved transcript evidence.

        Candidate semantic approvals are useful here as an index into exact source
        lines, but their meaning is not treated as confirmed research truth. The
        draft quotes preserved evidence and still requires explicit approval before
        any external Slack send.
        """
        meeting = self.db.fetchone("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        if not meeting:
            raise ValueError(f"Meeting not found: {meeting_id}")
        transcript_artifact_id = meeting["transcript_artifact_id"]
        if not transcript_artifact_id:
            raise ValueError(f"Meeting {meeting_id} has no transcript evidence")

        rows = self.db.fetchall(
            """SELECT * FROM approvals
               WHERE action_type = 'confirm_semantic_change'
               ORDER BY requested_at ASC, rowid ASC"""
        )
        discussion_points: list[str] = []
        next_commitments: list[str] = []
        seen_discussion: set[str] = set()
        seen_commitments: set[str] = set()
        for row in rows:
            payload = json.loads(row["action_payload_json"])
            if payload.get("meeting_id") != meeting_id:
                continue
            candidate = payload.get("candidate") or {}
            evidence = str(candidate.get("evidence") or "").strip()
            if not evidence:
                continue
            if payload.get("change_type") == "task":
                point = self._strip_speaker(evidence)
                if point and point not in seen_commitments:
                    seen_commitments.add(point)
                    next_commitments.append(point)
            else:
                point = self._strip_speaker(evidence)
                if point and point not in seen_discussion:
                    seen_discussion.add(point)
                    discussion_points.append(point)

        # If the conservative semantic index found nothing, preserve source truth by
        # using non-empty transcript lines verbatim instead of manufacturing a
        # summary. This makes the draft useful while keeping interpretation out.
        if not discussion_points and not next_commitments:
            transcript = self._read_transcript_artifact(transcript_artifact_id)
            for line in (part.strip() for part in transcript.splitlines()):
                if not line:
                    continue
                point = self._strip_speaker(line)
                if point and point not in seen_discussion:
                    seen_discussion.add(point)
                    discussion_points.append(point)

        if not discussion_points:
            discussion_points.append("逐字稿未擷取出明確的老師討論重點，請送出前人工確認。")
        if not next_commitments:
            next_commitments.append("逐字稿未擷取出明確的學生承諾事項，請送出前人工確認。")

        title = meeting["title"] or f"Advisor Meeting {meeting_id}"
        date_source = meeting["actual_ended_at"] or meeting["scheduled_at"] or utc_now()
        date_str = str(date_source)[:10]
        draft = generate_post_meeting_slack_draft(title, date_str, discussion_points, next_commitments)
        dedup_key = f"meeting-slack-draft:{meeting_id}:{transcript_artifact_id}"
        return self._create_slack_approval(meeting_id, draft, dedup_key=dedup_key)

    def _create_slack_approval(
        self,
        meeting_id: str,
        draft: str,
        *,
        dedup_key: Optional[str] = None,
    ) -> str:
        source = self.events.register_source("system", "Meeting Follow-up", "meeting-followup")
        approval_id = generate_id("AP-")
        event = self.events.record_event(
            event_type="approval.requested",
            source_id=source.id,
            payload={
                "id": approval_id,
                "action_type": "send_slack",
                "action_payload": {"channel": "advisor-dm", "text": draft, "meeting_id": meeting_id},
                "reason": "實驗室需知規定：meeting 結束後需將討論內容整理條列並透過 Slack 回報。",
                "risk_level": "medium",
                "estimated_cost": 0.0,
            },
            dedup_key=dedup_key,
        )
        apply_event(self.db, event)
        return str(event.payload["id"])

    def _read_transcript_artifact(self, artifact_id: str) -> str:
        artifact = self.db.fetchone("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
        if not artifact:
            raise ValueError(f"Transcript artifact not found: {artifact_id}")
        path = (self.repo_root / artifact["path"]).resolve()
        try:
            path.relative_to(self.repo_root)
        except ValueError as exc:
            raise ValueError(f"Transcript artifact escapes repository root: {artifact_id}") from exc
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Transcript artifact file missing: {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _strip_speaker(line: str) -> str:
        return re.sub(r"^[^:：]+[:：]\s*", "", line).strip()

    def _extract_semantics(self, text: str) -> dict[str, Any]:
        """Conservatively identify *candidates* from explicit transcript language.

        This is intentionally not an LLM substitute. It only recognizes narrow,
        evidence-bearing patterns and returns exact source lines for review.
        """
        decisions: list[dict[str, Any]] = []
        obligations: list[dict[str, Any]] = []
        tasks: list[dict[str, Any]] = []

        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(raw_lines) == 1:
            raw_lines = [part.strip() for part in re.split(r"(?=(?:Prof|Professor|老師|Student|學生)\s*[:：])", text) if part.strip()]

        for line in raw_lines:
            lower = line.lower()
            is_professor = bool(re.match(r"^(prof(?:essor)?|老師)\s*[:：]", line, re.IGNORECASE))
            is_student = bool(re.match(r"^(student|學生)\s*[:：]", line, re.IGNORECASE))
            spoken = re.sub(r"^[^:：]+[:：]\s*", "", line).strip()

            if is_professor and "baseline" in lower and re.search(r"可以先|先用|先當|採用|使用", spoken):
                decisions.append({
                    "statement": spoken,
                    "rationale": "Candidate extracted verbatim from advisor transcript; requires confirmation.",
                    "evidence": line,
                })

            # Explicit request/commitment cues plus an actionable verb. Schedule-only
            # changes such as "meeting 改到星期五" are deliberately excluded.
            if is_professor and re.search(r"下次|下週|記得|請|需要|要", spoken):
                if re.search(r"準備|完成|跑|比較|整理|分析|驗證|實作|帶.*來|看.*結果|做", spoken):
                    obligations.append({
                        "title": spoken,
                        "description": "Candidate obligation extracted verbatim from advisor transcript.",
                        "severity": "high",
                        "evidence": line,
                    })

            if is_student and re.search(r"我會|我這週會|會把|會完成|會先", spoken):
                if re.search(r"完成|跑|比較|整理|分析|驗證|實作|準備|做", spoken):
                    tasks.append({
                        "title": spoken,
                        "description": "Candidate self-commitment extracted verbatim from transcript.",
                        "priority": "high",
                        "agentability": "interactive",
                        "evidence": line,
                    })

        return {"decisions": decisions, "obligations": obligations, "tasks": tasks}
