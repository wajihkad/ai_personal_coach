from __future__ import annotations

# Agent loop tests — LLM API is always stubbed. Never calls the real API.

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from coach import agent
from coach.models import DailyCard, Domain


def _make_stub_client(tool_name: str, tool_input: dict) -> MagicMock:
    """Return a fake Anthropic client that returns a tool_use block."""
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.input = tool_input

    response = MagicMock()
    response.content = [tool_use_block]

    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_run_returns_daily_card(sample_profile, sample_checkin, tmp_path):
    stub_input = {
        "actions": [
            {"domain": "guitar", "description": "Practice C major scale", "duration_minutes": 20},
            {"domain": "chess", "description": "Solve 5 puzzles", "duration_minutes": 15},
        ],
        "motivation_note": "You had a great guitar session yesterday — keep the streak going!",
    }
    stub_client = _make_stub_client("daily_card", stub_input)

    with patch("coach.storage.settings") as mock_settings, \
         patch("coach.agent.storage.save_daily_card"):
        mock_settings.data_dir = tmp_path
        card = agent.run(
            user_text="Did some guitar today.",
            profile=sample_profile,
            checkins=[sample_checkin],
            client=stub_client,
            now=datetime(2026, 4, 10),  # Friday — but < 3 checkins this week → DailyCard
        )

    assert isinstance(card, DailyCard)
    assert len(card.actions) == 2
    assert card.actions[0].domain == Domain.GUITAR
    assert "streak" in card.motivation_note
