from __future__ import annotations

# Dataclasses and enums — the authoritative data contract for this project.
# Do not add serialization logic here; that belongs in storage.py.
# Do not define data structures in any other module.
#
# Domains are plain strings — users define them freely in profile.json or via
# the CLI. There is no hardcoded Domain enum.

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Level(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Status(Enum):
    DONE = "done"
    SKIPPED = "skipped"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class DomainProfile:
    domain: str
    level: Level
    goal: str
    hours_per_week: float
    notes: str = ""


@dataclass
class Action:
    domain: str
    description: str
    duration_minutes: int
    status: Status = Status.PENDING
    feedback: Optional[str] = None


@dataclass
class ProfileCard:
    user_name: str
    domains: list[DomainProfile]
    available_days: list[str]
    preferred_session_length: int
    learning_style: str
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DailyCard:
    date: datetime
    actions: list[Action]
    motivation_note: str
    generated_by_agent: bool = True


@dataclass
class WeeklyCard:
    week_start: datetime
    week_end: datetime
    domain_summaries: dict[str, str]
    completion_rate: dict[str, float]
    highlight: str
    next_week_focus: list[Action]


@dataclass
class MilestoneCard:
    date: datetime
    domain: str
    achievement: str
    next_challenge: str


@dataclass
class CheckIn:
    date: datetime
    completed_actions: list[Action]
    energy_level: int
    free_text: str
