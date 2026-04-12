from __future__ import annotations

# Dummy LLM client — used automatically when ANTHROPIC_API_KEY is not set.
# Returns plausible hardcoded responses so the full loop can be exercised
# without a real API key.

import random
from types import SimpleNamespace
from coach.models import ProfileCard, CheckIn


class DummyClient:
    """Mimics the anthropic.Anthropic client interface, returns fake tool-use blocks."""

    def __init__(self) -> None:
        self.messages = _DummyMessages()


class _DummyMessages:
    def create(self, *, tools: list, tool_choice: dict, messages: list, **kwargs) -> object:
        tool_name = tool_choice["name"]

        if tool_name == "daily_card":
            tool_input = _dummy_daily_input(messages)
        elif tool_name == "weekly_card":
            tool_input = _dummy_weekly_input()
        else:
            tool_input = _dummy_milestone_input()

        tool_use_block = SimpleNamespace(type="tool_use", input=tool_input)
        return SimpleNamespace(content=[tool_use_block])


# ---------------------------------------------------------------------------
# Fake outputs per card type
# ---------------------------------------------------------------------------

_GUITAR_ACTIONS = [
    ("Practice C major scale slowly with a metronome", 20),
    ("Work on chord transition: G → D → Em", 25),
    ("Play through your current song from start to finish", 30),
    ("Focus on fingerpicking pattern for verse section", 20),
]

_CHESS_ACTIONS = [
    ("Solve 5 tactical puzzles on Lichess", 20),
    ("Review the last game you lost — find your mistake", 15),
    ("Practice endgame: king and pawn vs king", 20),
    ("Study one opening line (e4 e5 Nf3 Nc6)", 25),
]

_CODING_ACTIONS = [
    ("Write the storage module and test it with a sample file", 30),
    ("Implement the agent loop step by step", 45),
    ("Read the Anthropic tool-use docs and run the example", 20),
    ("Refactor yesterday's code — pick one thing to simplify", 25),
]

_MOTIVATIONS = [
    "You showed up yesterday — that's already half the battle. Let's keep the momentum.",
    "Small consistent sessions beat marathon sessions every time. Today's focus is quality.",
    "You're building habits, not just skills. Each check-in counts.",
    "Progress is rarely linear. Trust the process and focus on today's actions.",
]


def _dummy_daily_input(messages: list) -> dict:
    actions = [
        {"domain": "guitar", "description": random.choice(_GUITAR_ACTIONS)[0],
         "duration_minutes": random.choice(_GUITAR_ACTIONS)[1]},
        {"domain": "chess", "description": random.choice(_CHESS_ACTIONS)[0],
         "duration_minutes": random.choice(_CHESS_ACTIONS)[1]},
    ]
    return {
        "actions": actions,
        "motivation_note": f"[DUMMY] {random.choice(_MOTIVATIONS)}",
    }


def _dummy_weekly_input() -> dict:
    return {
        "domain_summaries": {
            "guitar": "Solid week — you completed 3 out of 4 planned sessions.",
            "chess": "Lighter week on chess. Two puzzle sessions done.",
            "coding": "Good progress on the project setup.",
        },
        "completion_rate": {
            "guitar": 0.75,
            "chess": 0.5,
            "coding": 0.8,
        },
        "highlight": "[DUMMY] You finished a full run-through of your song for the first time!",
        "next_week_focus": [
            {"domain": "chess", "description": "Catch up on chess — aim for 3 puzzle sessions", "duration_minutes": 20},
            {"domain": "guitar", "description": "Start learning the bridge section", "duration_minutes": 25},
        ],
    }


def _dummy_milestone_input() -> dict:
    return {
        "domain": "guitar",
        "achievement": "[DUMMY] Completed 5 consecutive guitar sessions!",
        "next_challenge": "Learn a new chord progression and apply it to a song you like.",
    }
