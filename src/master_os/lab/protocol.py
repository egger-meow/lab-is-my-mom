"""Machine-readable protocol and operational rules for NYCU NLP Lab (Prof. An-Zi Yen)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LabChannels:
    """Official lab communication and resource links."""
    advisor_name: str = "顏安孜 (Prof. An-Zi Yen)"
    advisor_email: str = "azyen@nycu.edu.tw"
    advisor_webpage: str = "https://azyen0522.github.io/"
    meeting_url: str = "https://meet.google.com/jrh-oceu-hpu"
    shared_drive_url: str = "https://drive.google.com/drive/folders/1j3pMvCeAlL8gikpskaJV4Gtm7DA1sY9O?usp=sharing"
    seminar_sheet_url: str = "https://docs.google.com/spreadsheets/d/1oipua0MV9SDuHFPc7R8NREcT8723yjy_vky5OcS5v-s/edit?usp=sharing"
    slack_workspace: str = "NYCU NLP Lab"


@dataclass(frozen=True)
class IndividualMeetingFormat:
    """Individual weekly advisor meeting structure and expectations."""
    step1_review: str = "1~2 分鐘：簡要回顧上週進度與承諾事項"
    step2_agenda: str = "1~2 分鐘：說明這週要討論的事項"
    step3_discussion: str = "5~25 分鐘：報告和討論這週進度與實驗結果"
    table_guideline: str = "每一列是一個方法，每一行是評估指標 (e.g. accuracy, cost)，由上至下比較"
    diagram_guideline: str = "以簡易框架圖、流程圖輔助說明"
    findings_guideline: str = "自行解讀數據，條列 findings 與模型輸出範例，會議核心聚焦於 findings"
    post_meeting_slack_obligation: str = "當天 meeting 結束，請將討論的內容整理條列後，透過 Slack 傳給老師"


@dataclass(frozen=True)
class SeminarFormat:
    """Lab Seminar rules and presentation formats."""
    time: str = "每週一 13:30~14:10 (Google Meet)"
    day_of_week: str = "mon"
    start_time: str = "13:30"
    end_time: str = "14:10"
    timezone: str = "Asia/Taipei"
    presentation_duration_minutes: int = 30
    eligibility: str = "新生加入實驗室的第二個學期排入報告順序"
    survey_type: str = "Survey 類型：針對特定主題分享 5 篇以上論文，著重研究動機、框架、資料集與議題總結"
    deep_dive_type: str = "深入研讀類型：精讀長篇論文，分析動機、方法、實驗、優缺點、想對作者提的問題與自身解決方案"
    confirmation_rule: str = "輪到報告前需先與老師確認採取 Survey 還是 Deep-dive 形式"
    qa_rule: str = "報告結束後 QA：由下一次預定報告的同學提問，以及老師隨機點名兩位同學提問"


@dataclass(frozen=True)
class ComputeSafetyRules:
    """Strict resource bounds and billing hazard warnings."""
    openai_shared_policy: str = "使用各自 Project API key；超過每月上限需先估算 requests 與成本報備審核；輸出格式異常立刻停止"
    nchc_delete_container_warning: str = "實驗跑完記得刪除容器，否則會一直扣錢！扣款不會停止在個人額度 0 元或母錢包 0 元，可能產生高額欠費！"
    nchc_h100_policy: str = "需付費使用，使用前需先跟老師確認計畫類別與操作說明"


LAB_CHANNELS = LabChannels()
MEETING_FORMAT = IndividualMeetingFormat()
SEMINAR_FORMAT = SeminarFormat()
COMPUTE_SAFETY = ComputeSafetyRules()

# The student guide explicitly fixes Seminar at Monday 13:30–14:10.  Advisor
# meeting is weekly too, but the guide does not specify its weekday/time, so that
# cadence must come from the student as user-explicit state.
SEMINAR_WEEKLY_SPEC = {
    "day_of_week": SEMINAR_FORMAT.day_of_week,
    "start_time": SEMINAR_FORMAT.start_time,
    "end_time": SEMINAR_FORMAT.end_time,
    "timezone": SEMINAR_FORMAT.timezone,
}


def create_default_lab_schedules() -> list[dict[str, Any]]:
    """Standard recurring AI routines aligned with NYCU NLP Lab life."""
    return [
        {
            "name": "Weekly Seminar Readiness",
            "trigger_type": "time_cron",
            "trigger_spec": {"day_of_week": "mon", "hour": 10, "minute": 0},
            "agent_role": "seminar_agent",
            "prompt_template": "檢查當週 Seminar 輪替表與自己是否需要報告/提問，準備 QA 題庫或簡報進度",
            "autonomy_policy": {"dispatch_local": True, "external_actions": "approval"},
        },
        {
            "name": "Advisor Pre-Meeting Readiness & Pack",
            "trigger_type": "relative_meeting",
            "trigger_spec": {"meeting_kind": "advisor", "offset_minutes": -720},
            "agent_role": "meeting_agent",
            "prompt_template": "依每週 advisor meeting 固定時間計算 readiness，根據實驗結果與 Findings 產出個人 Meeting 簡報大綱與數據表格 (Excel/Markdown)",
            "autonomy_policy": {"dispatch_local": True, "external_actions": "approval"},
        },
        {
            "name": "Advisor Post-Meeting Digest to Slack",
            "trigger_type": "event",
            "trigger_spec": {"event_type": "meeting.completed"},
            "agent_role": "meeting_agent",
            "prompt_template": "依實驗室規定，將會議討論條列整理為 Slack 回報草稿，待使用者審批後傳送給老師",
            "autonomy_policy": {"dispatch_local": True, "external_actions": "approval"},
        },
        {
            "name": "NCHC & API Resource Burn Watchdog",
            "trigger_type": "interval",
            "trigger_spec": {"interval_minutes": 60},
            "agent_role": "critic",
            "prompt_template": "檢查國網中心有無未關閉的容器，以及 OpenAI API burn rate，預防扣款失控",
            "autonomy_policy": {"dispatch_local": True, "external_actions": "approval"},
        },
        {
            "name": "Weekly Research Progress & Critic",
            "trigger_type": "time_cron",
            "trigger_spec": {"day_of_week": "sun", "hour": 20, "minute": 0},
            "agent_role": "critic",
            "prompt_template": "評估全週研究進展，檢驗真實 Evidence 產出量與假進度警報 (Activity high, progress low)",
            "autonomy_policy": {"dispatch_local": True, "external_actions": "approval"},
        },
    ]


def generate_post_meeting_slack_draft(
    meeting_title: str,
    date_str: str,
    discussion_points: list[str],
    next_commitments: list[str],
) -> str:
    """Generate compliant post-meeting Slack update matching Prof. Yen's protocol."""
    lines = [
        f"老師好，以下是今天 ({date_str}) {meeting_title} 的討論整理與後續規劃：",
        "",
        "【今日討論重點】",
    ]
    for pt in discussion_points:
        lines.append(f"• {pt}")

    lines.append("")
    lines.append("【預計下週進度與 Commitments】")
    for com in next_commitments:
        lines.append(f"• {com}")

    lines.append("")
    lines.append("若有理解不完整或需要補充的地方，我會隨時再跟老師確認，謝謝老師！")
    return "\n".join(lines)
