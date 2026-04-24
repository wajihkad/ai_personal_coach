from __future__ import annotations

# Dummy LLM client — used automatically when OPENAI_API_KEY is not set.
# Returns plausible hardcoded responses so the full loop can be exercised
# without a real API key.

import json
import random
from types import SimpleNamespace


class DummyClient:
    """Mimics the openai.OpenAI client interface, returns fake tool-call responses."""

    def __init__(self) -> None:
        self.chat = _DummyChat()


class _DummyChat:
    def __init__(self) -> None:
        self.completions = _DummyCompletions()


class _DummyCompletions:
    def create(self, *, tools: list, tool_choice: dict, messages: list, **kwargs) -> object:
        tool_name = tool_choice["function"]["name"]
        # Extract the domain list from the tool schema the agent passed in
        domain_values = tools[0]["function"]["parameters"]["properties"].get(
            "actions", {}
        ).get("items", {}).get("properties", {}).get("domain", {}).get("enum", ["unknown"])

        if tool_name == "daily_card":
            tool_input = _dummy_daily_input(domain_values)
        elif tool_name == "weekly_card":
            tool_input = _dummy_weekly_input(domain_values)
        else:
            tool_input = _dummy_milestone_input(domain_values)

        # Mirror the OpenAI response shape: choices[0].message.tool_calls[0].function
        function = SimpleNamespace(name=tool_name, arguments=json.dumps(tool_input))
        tool_call = SimpleNamespace(function=function)
        message = SimpleNamespace(tool_calls=[tool_call])
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


# ---------------------------------------------------------------------------
# Fake outputs per card type
# ---------------------------------------------------------------------------

# Generic action templates — work for any domain name.
_GENERIC_ACTIONS = [
    ("Work on a focused practice session", 20),
    ("Review what you learned last time and build on it", 25),
    ("Pick one specific weak point and drill it", 30),
    ("Do a short, high-quality session — consistency matters", 20),
]

_MOTIVATIONS = [
    "You showed up yesterday — that's already half the battle. Let's keep the momentum.",
    "Small consistent sessions beat marathon sessions every time. Today's focus is quality.",
    "You're building habits, not just skills. Each check-in counts.",
    "Progress is rarely linear. Trust the process and focus on today's actions.",
]


def _dummy_action_for(domain: str) -> dict:
    description, duration = random.choice(_GENERIC_ACTIONS)
    return {"domain": domain, "description": description, "duration_minutes": duration}


def _dummy_daily_input(domain_values: list[str]) -> dict:
    # Pick up to 2 domains from the user's actual domain list
    chosen = random.sample(domain_values, min(2, len(domain_values)))
    return {
        "actions": [_dummy_action_for(d) for d in chosen],
        "motivation_note": f"[DUMMY] {random.choice(_MOTIVATIONS)}",
    }


def _dummy_weekly_input(domain_values: list[str]) -> dict:
    return {
        "domain_summaries": {d: f"Decent week on {d} — keep the habit going." for d in domain_values},
        "completion_rate": {d: round(random.uniform(0.4, 1.0), 2) for d in domain_values},
        "highlight": "[DUMMY] You stayed consistent across all your domains this week!",
        "next_week_focus": [_dummy_action_for(d) for d in domain_values[:2]],
    }


def _dummy_milestone_input(domain_values: list[str]) -> dict:
    domain = domain_values[0] if domain_values else "unknown"
    return {
        "domain": domain,
        "achievement": f"[DUMMY] Completed 5 consecutive {domain} sessions!",
        "next_challenge": f"Push to the next level in {domain} — pick a harder challenge.",
    }
