from __future__ import annotations

# Dataclasses and enums — the authoritative data contract for this project.
# Do not add serialization logic here; that belongs in storage.py.
# Do not define data structures in any other module.

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Domain(Enum):
    GUITAR = "guitar"
    CHESS = "chess"
    CODING = "coding"


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
    domain: Domain
    level: Level
    goal: str
    hours_per_week: float
    notes: str = ""


@dataclass
class Action:
    domain: Domain
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
    domain_summaries: dict[Domain, str]
    completion_rate: dict[Domain, float]
    highlight: str
    next_week_focus: list[Action]


@dataclass
class MilestoneCard:
    date: datetime
    domain: Domain
    achievement: str
    next_challenge: str


@dataclass
class CheckIn:
    date: datetime
    completed_actions: list[Action]
    energy_level: int
    free_text: str
