from __future__ import annotations

# Read and write all data to local JSON files.
# Returns None on missing files — never raises on absence.
# All writes are atomic (write to .tmp, then os.replace).

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from coach.config import settings
from coach.models import (
    Action,
    CheckIn,
    DailyCard,
    Domain,
    DomainProfile,
    Level,
    MilestoneCard,
    ProfileCard,
    Status,
    WeeklyCard,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> Optional[dict | list]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to read %s", path)
        return None


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_action(a: Action) -> dict:
    return {
        "domain": a.domain.value,
        "description": a.description,
        "duration_minutes": a.duration_minutes,
        "status": a.status.value,
        "feedback": a.feedback,
    }


def _deserialize_action(d: dict) -> Action:
    return Action(
        domain=Domain(d["domain"]),
        description=d["description"],
        duration_minutes=d["duration_minutes"],
        status=Status(d["status"]),
        feedback=d.get("feedback"),
    )


# ---------------------------------------------------------------------------
# ProfileCard
# ---------------------------------------------------------------------------

def _profile_path() -> Path:
    return settings.data_dir / "profile.json"


def save_profile(profile: ProfileCard) -> None:
    data = {
        "user_name": profile.user_name,
        "domains": [
            {
                "domain": dp.domain.value,
                "level": dp.level.value,
                "goal": dp.goal,
                "hours_per_week": dp.hours_per_week,
                "notes": dp.notes,
            }
            for dp in profile.domains
        ],
        "available_days": profile.available_days,
        "preferred_session_length": profile.preferred_session_length,
        "learning_style": profile.learning_style,
        "last_updated": profile.last_updated.isoformat(),
    }
    _atomic_write(_profile_path(), data)


def load_profile() -> Optional[ProfileCard]:
    data = _read_json(_profile_path())
    if data is None:
        return None
    return ProfileCard(
        user_name=data["user_name"],
        domains=[
            DomainProfile(
                domain=Domain(d["domain"]),
                level=Level(d["level"]),
                goal=d["goal"],
                hours_per_week=d["hours_per_week"],
                notes=d.get("notes", ""),
            )
            for d in data["domains"]
        ],
        available_days=data["available_days"],
        preferred_session_length=data["preferred_session_length"],
        learning_style=data["learning_style"],
        last_updated=datetime.fromisoformat(data["last_updated"]),
    )


# ---------------------------------------------------------------------------
# CheckIn
# ---------------------------------------------------------------------------

def _checkin_path(date: datetime) -> Path:
    return settings.data_dir / "checkins" / f"{date.strftime('%Y-%m-%d')}.json"


def save_checkin(checkin: CheckIn) -> None:
    data = {
        "date": checkin.date.isoformat(),
        "completed_actions": [_serialize_action(a) for a in checkin.completed_actions],
        "energy_level": checkin.energy_level,
        "free_text": checkin.free_text,
    }
    _atomic_write(_checkin_path(checkin.date), data)


def load_checkin(date: datetime) -> Optional[CheckIn]:
    data = _read_json(_checkin_path(date))
    if data is None:
        return None
    return CheckIn(
        date=datetime.fromisoformat(data["date"]),
        completed_actions=[_deserialize_action(a) for a in data["completed_actions"]],
        energy_level=data["energy_level"],
        free_text=data["free_text"],
    )


def load_recent_checkins(n: int) -> list[CheckIn]:
    checkins_dir = settings.data_dir / "checkins"
    if not checkins_dir.exists():
        return []
    paths = sorted(checkins_dir.glob("*.json"), reverse=True)[:n]
    results = []
    for p in paths:
        data = _read_json(p)
        if data:
            results.append(CheckIn(
                date=datetime.fromisoformat(data["date"]),
                completed_actions=[_deserialize_action(a) for a in data["completed_actions"]],
                energy_level=data["energy_level"],
                free_text=data["free_text"],
            ))
    return results


# ---------------------------------------------------------------------------
# DailyCard
# ---------------------------------------------------------------------------

def _daily_card_path(date: datetime) -> Path:
    return settings.data_dir / "cards" / "daily" / f"{date.strftime('%Y-%m-%d')}.json"


def save_daily_card(card: DailyCard) -> None:
    data = {
        "date": card.date.isoformat(),
        "actions": [_serialize_action(a) for a in card.actions],
        "motivation_note": card.motivation_note,
        "generated_by_agent": card.generated_by_agent,
    }
    _atomic_write(_daily_card_path(card.date), data)


def load_daily_card(date: datetime) -> Optional[DailyCard]:
    data = _read_json(_daily_card_path(date))
    if data is None:
        return None
    return DailyCard(
        date=datetime.fromisoformat(data["date"]),
        actions=[_deserialize_action(a) for a in data["actions"]],
        motivation_note=data["motivation_note"],
        generated_by_agent=data["generated_by_agent"],
    )


# ---------------------------------------------------------------------------
# WeeklyCard
# ---------------------------------------------------------------------------

def _weekly_card_path(date: datetime) -> Path:
    week = date.strftime("%Y-W%W")
    return settings.data_dir / "cards" / "weekly" / f"{week}.json"


def save_weekly_card(card: WeeklyCard) -> None:
    data = {
        "week_start": card.week_start.isoformat(),
        "week_end": card.week_end.isoformat(),
        "domain_summaries": {k.value: v for k, v in card.domain_summaries.items()},
        "completion_rate": {k.value: v for k, v in card.completion_rate.items()},
        "highlight": card.highlight,
        "next_week_focus": [_serialize_action(a) for a in card.next_week_focus],
    }
    _atomic_write(_weekly_card_path(card.week_start), data)


def load_weekly_card(date: datetime) -> Optional[WeeklyCard]:
    data = _read_json(_weekly_card_path(date))
    if data is None:
        return None
    return WeeklyCard(
        week_start=datetime.fromisoformat(data["week_start"]),
        week_end=datetime.fromisoformat(data["week_end"]),
        domain_summaries={Domain(k): v for k, v in data["domain_summaries"].items()},
        completion_rate={Domain(k): v for k, v in data["completion_rate"].items()},
        highlight=data["highlight"],
        next_week_focus=[_deserialize_action(a) for a in data["next_week_focus"]],
    )


# ---------------------------------------------------------------------------
# MilestoneCard
# ---------------------------------------------------------------------------

def _milestone_card_path(date: datetime, domain: Domain) -> Path:
    return (
        settings.data_dir
        / "cards"
        / "milestone"
        / f"{date.strftime('%Y-%m-%d')}-{domain.value}.json"
    )


def save_milestone_card(card: MilestoneCard) -> None:
    data = {
        "date": card.date.isoformat(),
        "domain": card.domain.value,
        "achievement": card.achievement,
        "next_challenge": card.next_challenge,
    }
    _atomic_write(_milestone_card_path(card.date, card.domain), data)


def load_milestone_card(date: datetime, domain: Domain) -> Optional[MilestoneCard]:
    data = _read_json(_milestone_card_path(date, domain))
    if data is None:
        return None
    return MilestoneCard(
        date=datetime.fromisoformat(data["date"]),
        domain=Domain(data["domain"]),
        achievement=data["achievement"],
        next_challenge=data["next_challenge"],
    )
