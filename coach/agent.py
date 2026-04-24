from __future__ import annotations

# Agent loop: loads context, calls the LLM, returns a structured card.
# The LLM client is injected so tests can substitute a stub.

import logging
from datetime import datetime, timedelta
from typing import Optional, Union

import json

import openai

from coach.config import settings
from coach.dummy import DummyClient
from coach.models import (
    Action,
    CheckIn,
    DailyCard,
    MilestoneCard,
    ProfileCard,
    Status,
    WeeklyCard,
)
from coach.prompts import (
    SYSTEM_PROMPT,
    build_daily_card_tool,
    build_milestone_card_tool,
    build_user_message,
    build_weekly_card_tool,
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
            domain=a["domain"],
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
        domain_summaries=tool_input["domain_summaries"],
        completion_rate=tool_input["completion_rate"],
        highlight=tool_input["highlight"],
        next_week_focus=[
            Action(
                domain=a["domain"],
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
        domain=tool_input["domain"],
        achievement=tool_input["achievement"],
        next_challenge=tool_input["next_challenge"],
    )


def run(
    user_text: str,
    profile: ProfileCard,
    checkins: list[CheckIn],
    client: Optional[openai.OpenAI] = None,
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
    client : openai.OpenAI, optional
        LLM client. Defaults to a real OpenAI client. Inject a stub for tests.
    now : datetime, optional
        Current time. Defaults to datetime.now(). Override in tests.
    """
    if client is None:
        if settings.openai_api_key:
            client = openai.OpenAI(api_key=settings.openai_api_key)
        else:
            logger.warning("OPENAI_API_KEY not set — using dummy client. Output is fake.")
            client = DummyClient()
    if now is None:
        now = datetime.now()

    domain_values = [dp.domain for dp in profile.domains]
    card_type = _select_card_type(now, checkins)
    tool = {
        "daily": build_daily_card_tool(domain_values),
        "weekly": build_weekly_card_tool(domain_values),
        "milestone": build_milestone_card_tool(domain_values),
    }[card_type]
    tool_name = tool["function"]["name"]

    user_message = build_user_message(profile, checkins, user_text)

    # Retry up to 3 times with exponential backoff
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            break
        except openai.APIError as e:
            last_error = e
            wait = 2**attempt
            logger.warning("API call failed (attempt %d/3), retrying in %ds: %s", attempt + 1, wait, e)
            import time
            time.sleep(wait)
    else:
        raise RuntimeError(f"LLM API call failed after 3 attempts: {last_error}") from last_error

    tool_call = response.choices[0].message.tool_calls[0]
    tool_input = json.loads(tool_call.function.arguments)

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
