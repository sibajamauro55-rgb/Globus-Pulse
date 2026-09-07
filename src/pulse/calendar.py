from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from pulse.models import Piece


def load_calendar(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def next_slot(session: Session, cal: dict, now: datetime | None = None) -> datetime:
    tz = ZoneInfo(cal.get("timezone") or "America/Mexico_City")
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    min_gap = timedelta(hours=int(cal.get("min_hours_between_posts") or 18))
    last = session.scalar(select(Piece.scheduled_at).order_by(Piece.scheduled_at.desc()).limit(1))
    candidate = now + timedelta(minutes=2)
    if last:
        last = last if last.tzinfo else last.replace(tzinfo=tz)
        floor = last.astimezone(tz) + min_gap
        if floor > candidate:
            candidate = floor
    if candidate.hour < 8:
        candidate = candidate.replace(hour=9, minute=0, second=0, microsecond=0)
    return candidate


def weekday_key(dt: datetime) -> str:
    return ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[dt.weekday()]


def plan_for(cal: dict, when: datetime) -> dict:
    key = weekday_key(when)
    plan = (cal.get("weekday_plan") or {}).get(key) or {}
    categories = list(plan.get("categories") or ["commercial"])
    formats = list(plan.get("formats") or ["post"])
    return {"categories": categories, "formats": formats}
