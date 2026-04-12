from __future__ import annotations

# Single source of truth for all configuration.
# All other modules import from here — never read config.toml or os.environ directly.

import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config.toml"


@dataclass
class Settings:
    # Paths
    data_dir: Path
    log_dir: Path

    # Scheduling
    week_end_day: str
    morning_run_time: str
    evening_nudge_time: str

    # Agent behaviour
    milestone_streak_threshold: int
    max_daily_actions: int
    history_window_days: int

    # Feature flags
    enable_calendar: bool
    enable_todoist: bool
    enable_telegram: bool
    enable_lichess: bool

    # Secrets (from .env)
    openai_api_key: str


def _load() -> Settings:
    with open(_CONFIG_PATH, "rb") as f:
        raw = tomllib.load(f)

    coach = raw["coach"]
    tools = raw["tools"]

    api_key = os.environ.get("OPENAI_API_KEY", "")
    # Empty key is allowed — agent.py will fall back to the dummy client.

    return Settings(
        data_dir=_ROOT / coach["data_dir"],
        log_dir=_ROOT / coach["log_dir"],
        week_end_day=coach["week_end_day"].lower(),
        morning_run_time=coach["morning_run_time"],
        evening_nudge_time=coach["evening_nudge_time"],
        milestone_streak_threshold=int(coach["milestone_streak_threshold"]),
        max_daily_actions=int(coach["max_daily_actions"]),
        history_window_days=int(coach["history_window_days"]),
        enable_calendar=bool(tools["enable_calendar"]),
        enable_todoist=bool(tools["enable_todoist"]),
        enable_telegram=bool(tools["enable_telegram"]),
        enable_lichess=bool(tools["enable_lichess"]),
        openai_api_key=api_key,
    )


settings = _load()
