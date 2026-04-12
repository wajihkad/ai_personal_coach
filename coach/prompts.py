from __future__ import annotations

# All system prompts and LLM tool schemas live here.
# No f-string prompts in other modules — build them here and import.

from coach.models import CheckIn, ProfileCard


SYSTEM_PROMPT = """\
You are a personal AI life coach. Your role is to help the user make consistent \
progress across their learning domains (e.g. guitar, chess, coding).

Rules you must follow:
- Always produce a structured card as output — never a free-form reply alone.
- Read the user's profile and recent check-ins carefully before deciding what to recommend.
- Reason across all active domains simultaneously — balance load, avoid neglecting any domain.
- Keep recommendations realistic and specific to the user's level and available time.
- When writing a motivation_note, reference something concrete from the user's recent history.
- Never suggest more actions than max_daily_actions (default: 3).
"""


def build_user_message(profile: ProfileCard, checkins: list[CheckIn], user_text: str) -> str:
    lines = [
        "## User Profile",
        f"Name: {profile.user_name}",
        f"Available days: {', '.join(profile.available_days)}",
        f"Preferred session length: {profile.preferred_session_length} min",
        f"Learning style: {profile.learning_style}",
        "",
        "### Domains",
    ]
    for dp in profile.domains:
        lines.append(
            f"- {dp.domain.value} | Level: {dp.level.value} | "
            f"Goal: {dp.goal} | {dp.hours_per_week}h/week"
            + (f" | Notes: {dp.notes}" if dp.notes else "")
        )

    if checkins:
        lines += ["", "## Recent Check-ins (newest first)"]
        for ci in checkins:
            lines.append(f"\n### {ci.date.strftime('%Y-%m-%d')} — energy {ci.energy_level}/5")
            lines.append(ci.free_text)
            for a in ci.completed_actions:
                lines.append(
                    f"  - [{a.status.value}] {a.domain.value}: {a.description} "
                    f"({a.duration_minutes}min)"
                    + (f" → {a.feedback}" if a.feedback else "")
                )

    lines += ["", "## Today's Check-in", user_text]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool schemas — one per card type
# ---------------------------------------------------------------------------

DAILY_CARD_TOOL = {
    "name": "daily_card",
    "description": "Produce a DailyCard with 2–3 prioritised actions and a personalised motivation note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "actions": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "enum": ["guitar", "chess", "coding"]},
                        "description": {"type": "string"},
                        "duration_minutes": {"type": "integer", "minimum": 5},
                    },
                    "required": ["domain", "description", "duration_minutes"],
                },
            },
            "motivation_note": {
                "type": "string",
                "description": "A short, specific motivational note referencing the user's recent history.",
            },
        },
        "required": ["actions", "motivation_note"],
    },
}

WEEKLY_CARD_TOOL = {
    "name": "weekly_card",
    "description": "Produce a WeeklyCard summarising the week and setting focus for next week.",
    "input_schema": {
        "type": "object",
        "properties": {
            "domain_summaries": {
                "type": "object",
                "description": "Narrative summary per domain (domain value as key).",
                "additionalProperties": {"type": "string"},
            },
            "completion_rate": {
                "type": "object",
                "description": "Completion rate 0.0–1.0 per domain (domain value as key).",
                "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "highlight": {
                "type": "string",
                "description": "The single most notable positive event of the week.",
            },
            "next_week_focus": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "enum": ["guitar", "chess", "coding"]},
                        "description": {"type": "string"},
                        "duration_minutes": {"type": "integer", "minimum": 5},
                    },
                    "required": ["domain", "description", "duration_minutes"],
                },
            },
        },
        "required": ["domain_summaries", "completion_rate", "highlight", "next_week_focus"],
    },
}

MILESTONE_CARD_TOOL = {
    "name": "milestone_card",
    "description": "Produce a MilestoneCard celebrating a user achievement and setting the next challenge.",
    "input_schema": {
        "type": "object",
        "properties": {
            "domain": {"type": "string", "enum": ["guitar", "chess", "coding"]},
            "achievement": {
                "type": "string",
                "description": "Concrete description of what the user achieved.",
            },
            "next_challenge": {
                "type": "string",
                "description": "Specific, domain-appropriate next challenge to aim for.",
            },
        },
        "required": ["domain", "achievement", "next_challenge"],
    },
}
