"""Weekly lab meeting cadence helpers.

The lab has recurring meeting rhythms.  Normal weekly meetings are represented as
recurrence rules; concrete meeting rows are reserved for history and rare one-off
meetings.  This keeps scheduler timing derived from the weekly truth instead of
asking the user to re-enter a date every week.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from master_os.core.database import MasterDatabase

WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
WEEKDAY_LABELS = {
    "mon": "週一", "tue": "週二", "wed": "週三", "thu": "週四",
    "fri": "週五", "sat": "週六", "sun": "週日",
}


def validate_weekly_spec(spec: dict[str, Any]) -> dict[str, Any]:
    day = str(spec.get("day_of_week") or "").lower().strip()
    if day not in WEEKDAYS:
        raise ValueError("day_of_week must be mon..sun")
    start_time = str(spec.get("start_time") or "").strip()
    try:
        hour_text, minute_text = start_time.split(":", 1)
        hour, minute = int(hour_text), int(minute_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("start_time must be HH:MM") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("start_time must be a valid 24-hour HH:MM")
    zone_name = str(spec.get("timezone") or "Asia/Taipei").strip()
    try:
        ZoneInfo(zone_name)
    except Exception as exc:
        raise ValueError(f"invalid timezone: {zone_name}") from exc
    result = {
        "day_of_week": day,
        "start_time": f"{hour:02d}:{minute:02d}",
        "timezone": zone_name,
    }
    if spec.get("end_time"):
        end = str(spec["end_time"]).strip()
        try:
            eh, em = (int(part) for part in end.split(":", 1))
        except (ValueError, AttributeError) as exc:
            raise ValueError("end_time must be HH:MM") from exc
        if not (0 <= eh <= 23 and 0 <= em <= 59):
            raise ValueError("end_time must be a valid 24-hour HH:MM")
        result["end_time"] = f"{eh:02d}:{em:02d}"
    return result


def next_weekly_occurrence(spec: dict[str, Any], now: Optional[datetime] = None) -> datetime:
    """Return the next occurrence strictly after ``now`` as UTC."""
    normalized = validate_weekly_spec(spec)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    zone = ZoneInfo(normalized["timezone"])
    local_now = current.astimezone(zone)
    hour, minute = (int(part) for part in normalized["start_time"].split(":"))
    days_ahead = (WEEKDAYS[normalized["day_of_week"]] - local_now.weekday()) % 7
    date = (local_now + timedelta(days=days_ahead)).date()
    candidate = datetime(date.year, date.month, date.day, hour, minute, tzinfo=zone)
    if candidate <= local_now:
        candidate += timedelta(days=7)
    return candidate.astimezone(timezone.utc)


def occurrence_id(kind: str, occurrence: datetime, spec: dict[str, Any]) -> str:
    zone = ZoneInfo(validate_weekly_spec(spec)["timezone"])
    local = occurrence.astimezone(zone)
    prefix = "ADV" if kind == "advisor" else "SEM" if kind == "lab_seminar" else kind.upper()[:6]
    return f"M-{prefix}-{local.strftime('%Y%m%d')}"


def resolved_weekly_spec(db: MasterDatabase, kind: str) -> Optional[dict[str, Any]]:
    """Resolve the highest-authority user/source weekly recurrence assertion."""
    row = db.fetchone(
        """SELECT value_json FROM assertions
           WHERE subject_type='meeting_routine' AND subject_id=? AND field='weekly_spec' AND status='active'
           ORDER BY authority DESC, confidence DESC, valid_from DESC, rowid DESC LIMIT 1""",
        (kind,),
    )
    if not row:
        return None
    value = json.loads(row["value_json"])
    return validate_weekly_spec(value) if isinstance(value, dict) else None


def routine_occurrence(kind: str, title: str, spec: dict[str, Any], *, now: Optional[datetime] = None) -> dict[str, Any]:
    occurrence = next_weekly_occurrence(spec, now)
    normalized = validate_weekly_spec(spec)
    return {
        "id": occurrence_id(kind, occurrence, normalized),
        "kind": kind,
        "title": title,
        "scheduled_at": occurrence.isoformat(),
        "status": "scheduled",
        "recurring": True,
        "weekly_spec": normalized,
    }
