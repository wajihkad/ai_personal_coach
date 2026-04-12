from __future__ import annotations

# Agent loop: loads context, calls the LLM, returns a structured card.
# The LLM client is injected so tests can substitute a stub.

import logging
from datetime import datetime, timedelta
from typing import Optional, Union

import anthropic

from coach.config import settings
from coach.dummy import DummyClient
from coach.models import (
    Action,
    CheckIn,
    DailyCard,
    Domain,
    MilestoneCard,
    ProfileCard,
    Status,
    WeeklyCard,
)
from coach.prompts import (
    DAILY_CARD_TOOL,
    MILESTONE_CARD_TOOL,
    SYSTEM_PROMPT,
    WEEKLY_CARD_TOOL,
    build_user_message,
)
from coach import storage

logger = logging.getLogger(__name__)

Card = Union[DailyCard, WeeklyCard, MilestoneCard]


def _select_card_type(now: datetime, checkins: list[CheckIn]) -> str:
    """Decide which card type to produce based on day and recent history."""
    is_week_end = now.strftime("%A").lower() == settings.week_end_day
    week_start = now - timedelta(days=now.weekday())
    week_checkins = [c for c in checkins if c.date >= week_start]

    if is_week_end and len(week_checkins) >= 3:
        return "weekly"
    return "daily"


def _build_daily_card(now: datetime, tool_input: dict) -> DailyCard:
    actions = [
        Action(
            domain=Domain(a["domain"]),
            description=a["description"],
            duration_minutes=a["duration_minutes"],
            status=Status.PENDING,
        )
        for a in tool_input["actions"]
    ]
    return DailyCard(
        date=now,
        actions=actions,
        motivation_note=tool_input["motivation_note"],
    )


def _build_weekly_card(now: datetime, tool_input: dict) -> WeeklyCard:
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    return WeeklyCard(
        week_start=week_start,
        week_end=week_end,
        domain_summaries={Domain(k): v for k, v in tool_input["domain_summaries"].items()},
        completion_rate={Domain(k): v for k, v in tool_input["completion_rate"].items()},
        highlight=tool_input["highlight"],
        next_week_focus=[
            Action(
                domain=Domain(a["domain"]),
                description=a["description"],
                duration_minutes=a["duration_minutes"],
                status=Status.PENDING,
            )
            for a in tool_input["next_week_focus"]
        ],
    )


def _build_milestone_card(now: datetime, tool_input: dict) -> MilestoneCard:
    return MilestoneCard(
        date=now,
        domain=Domain(tool_input["domain"]),
        achievement=tool_input["achievement"],
        next_challenge=tool_input["next_challenge"],
    )


def run(
    user_text: str,
    profile: ProfileCard,
    checkins: list[CheckIn],
    client: Optional[anthropic.Anthropic] = None,
    now: Optional[datetime] = None,
) -> Card:
    """
    Core agent loop. Returns a Card (Daily, Weekly, or Milestone).

    Parameters
    ----------
    user_text : str
        The user's natural-language check-in message.
    profile : ProfileCard
        The user's current profile.
    checkins : list[CheckIn]
        Recent check-ins (newest first), up to history_window_days.
    client : anthropic.Anthropic, optional
        LLM client. Defaults to a real Anthropic client. Inject a stub for tests.
    now : datetime, optional
        Current time. Defaults to datetime.now(). Override in tests.
    """
    if client is None:
        if settings.anthropic_api_key:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            logger.warning("ANTHROPIC_API_KEY not set — using dummy client. Output is fake.")
            client = DummyClient()
    if now is None:
        now = datetime.now()

    card_type = _select_card_type(now, checkins)
    tool = {
        "daily": DAILY_CARD_TOOL,
        "weekly": WEEKLY_CARD_TOOL,
        "milestone": MILESTONE_CARD_TOOL,
    }[card_type]

    user_message = build_user_message(profile, checkins, user_text)

    # Retry up to 3 times with exponential backoff
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool["name"]},
                messages=[{"role": "user", "content": user_message}],
            )
            break
        except anthropic.APIError as e:
            last_error = e
            wait = 2**attempt
            logger.warning("API call failed (attempt %d/3), retrying in %ds: %s", attempt + 1, wait, e)
            import time
            time.sleep(wait)
    else:
        raise RuntimeError(f"LLM API call failed after 3 attempts: {last_error}") from last_error

    tool_use = next(b for b in response.content if b.type == "tool_use")
    tool_input = tool_use.input

    if card_type == "daily":
        card: Card = _build_daily_card(now, tool_input)
        storage.save_daily_card(card)  # type: ignore[arg-type]
    elif card_type == "weekly":
        card = _build_weekly_card(now, tool_input)
        storage.save_weekly_card(card)  # type: ignore[arg-type]
    else:
        card = _build_milestone_card(now, tool_input)
        storage.save_milestone_card(card)  # type: ignore[arg-type]

    return card
