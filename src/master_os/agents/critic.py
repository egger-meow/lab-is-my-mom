"""Master Health and Research Velocity Critic for Master OS."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from master_os.core.database import MasterDatabase


@dataclass
class MasterHealthReport:
    """Diagnostic report evaluating research velocity, commitments, and fake progress."""
    research_velocity: float  # Scale 0.0 - 10.0
    evidence_count: int
    findings_count: int
    completed_experiments: int
    active_obligations_count: int
    overdue_obligations_count: int
    fake_progress_warning: bool
    warning_message: str
    resource_burn_warnings: list[str]


class MasterCritic:
    """Audits graduate school progress to prevent the 'busy but zero research velocity' trap."""

    def __init__(self, db: MasterDatabase) -> None:
        self.db = db

    def evaluate_health(self) -> MasterHealthReport:
        # 1. Count findings & evidence
        findings_row = self.db.fetchone("SELECT COUNT(*) as cnt FROM findings WHERE status IN ('validated', 'candidate')")
        findings_count = findings_row["cnt"] if findings_row else 0

        exp_row = self.db.fetchone("SELECT COUNT(*) as cnt FROM experiments WHERE status = 'completed' AND validity_status = 'valid'")
        completed_exps = exp_row["cnt"] if exp_row else 0

        # 2. Count active and actually overdue obligations. Deadline strings are
        # parsed as instants rather than compared lexically so equivalent offsets
        # do not produce different health results.
        active_rows = self.db.fetchall(
            "SELECT id, due_at FROM obligations WHERE status IN ('pending', 'in_progress')"
        )
        active_obs = len(active_rows)
        now = datetime.now(timezone.utc)
        overdue_obs = 0
        for row in active_rows:
            due_at = row["due_at"]
            if not due_at:
                continue
            try:
                due = self._parse_time(due_at)
            except (TypeError, ValueError):
                # Invalid external metadata must not take down the health daemon.
                # The malformed value remains visible in canonical state for repair.
                continue
            if due < now:
                overdue_obs += 1

        # 3. Check tasks completed
        tasks_row = self.db.fetchone("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'completed'")
        completed_tasks = tasks_row["cnt"] if tasks_row else 0

        # 4. Check for fake progress trap: High task activity but 0 experimental evidence
        fake_progress = False
        warning_msg = "研究節奏良好，持續產生可驗證的證據與進展。"

        if completed_tasks >= 3 and (findings_count == 0 and completed_exps == 0):
            fake_progress = True
            warning_msg = (
                "⚠ 警報：活動量高，但研究實質進度偏低 (Activity high, research progress low)！"
                f"已完成 {completed_tasks} 個任務，但尚未產出任何驗證的實驗數據或 Findings。"
                "請警惕陷入繁瑣程式碼或閱讀筆記，優先鎖定關鍵 Baseline 實驗與 Hypothesis 驗證！"
            )

        # 5. Calculate velocity score
        raw_score = (findings_count * 2.5) + (completed_exps * 3.0) + (completed_tasks * 0.5)
        if fake_progress:
            raw_score = min(raw_score, 3.5)
        velocity = min(10.0, max(1.0, raw_score))

        # 6. Check compute & resource burn
        burn_warnings = []
        nchc = self.db.fetchone("SELECT * FROM lab_resources WHERE resource_type = 'nchc'")
        if nchc and nchc["burn_rate_warning"]:
            burn_warnings.append(
                "⚠ 國網中心安全警報：偵測到可能有未關閉的容器在背景扣款！"
                "老師需知三度提醒：「實驗跑完記得刪除容器，否則會一直扣錢」！"
            )

        openai = self.db.fetchone("SELECT * FROM lab_resources WHERE resource_type = 'openai'")
        if openai and openai["quota_limit"] > 0:
            pct = (openai["quota_used"] / openai["quota_limit"]) * 100
            if pct > 85:
                burn_warnings.append(
                    f"⚠ OpenAI 額度警報：實驗室 Project API 額度已使用 {pct:.1f}%，超過上限需先向老師估算報備！"
                )

        return MasterHealthReport(
            research_velocity=round(velocity, 1),
            evidence_count=findings_count + completed_exps,
            findings_count=findings_count,
            completed_experiments=completed_exps,
            active_obligations_count=active_obs,
            overdue_obligations_count=overdue_obs,
            fake_progress_warning=fake_progress,
            warning_message=warning_msg,
            resource_burn_warnings=burn_warnings,
        )

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
