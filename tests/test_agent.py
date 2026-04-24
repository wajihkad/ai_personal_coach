from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock

from coach import agent
from coach.models import DailyCard


def _make_stub_client(tool_input: dict) -> MagicMock:
    function = MagicMock()
    function.arguments = json.dumps(tool_input)
    tool_call = MagicMock()
    tool_call.function = function
    message = MagicMock()
    message.tool_calls = [tool_call]
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


def test_run_returns_daily_card(sample_profile, sample_checkin):
    stub_input = {
        "actions": [
            {"domain": "guitar", "description": "Practice C major scale", "duration_minutes": 20},
            {"domain": "chess", "description": "Solve 5 puzzles", "duration_minutes": 15},
        ],
        "motivation_note": "You had a great guitar session yesterday — keep the streak going!",
    }
    stub_client = _make_stub_client(stub_input)

    with MagicMock() as mock_storage:
        card = agent.run(
            user_text="Did some guitar today.",
            profile=sample_profile,
            checkins=[sample_checkin],
            client=stub_client,
            now=datetime(2026, 4, 10),
        )

    assert isinstance(card, DailyCard)
    assert len(card.actions) == 2
    assert card.actions[0].domain == "guitar"
    assert "streak" in card.motivation_note
