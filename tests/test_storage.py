from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from coach.models import (
    Action,
    CheckIn,
    DailyCard,
    Domain,
    DomainProfile,
    Level,
    MilestoneCard,
    ProfileCard,
    Status,
)
from coach import storage


@pytest.fixture(autouse=True)
def patch_data_dir(tmp_path, monkeypatch):
    """Redirect all storage reads/writes to a temporary directory."""
    monkeypatch.setattr("coach.storage.settings", type("S", (), {"data_dir": tmp_path, "log_dir": tmp_path / "logs"})())


def test_save_and_load_profile(sample_profile, tmp_path):
    with patch("coach.storage.settings") as mock_settings:
        mock_settings.data_dir = tmp_path
        storage.save_profile(sample_profile)
        loaded = storage.load_profile()
    assert loaded is not None
    assert loaded.user_name == sample_profile.user_name
    assert loaded.domains[0].domain == Domain.GUITAR


def test_load_missing_profile_returns_none(tmp_path):
    with patch("coach.storage.settings") as mock_settings:
        mock_settings.data_dir = tmp_path
        result = storage.load_profile()
    assert result is None


def test_save_and_load_checkin(sample_checkin, tmp_path):
    with patch("coach.storage.settings") as mock_settings:
        mock_settings.data_dir = tmp_path
        storage.save_checkin(sample_checkin)
        loaded = storage.load_checkin(sample_checkin.date)
    assert loaded is not None
    assert loaded.energy_level == sample_checkin.energy_level
    assert loaded.free_text == sample_checkin.free_text


def test_save_and_load_daily_card(tmp_path):
    actions = [Action(domain=Domain.GUITAR, description="Scales", duration_minutes=20)]
    card = DailyCard(date=datetime(2026, 4, 10), actions=actions, motivation_note="Go!")
    with patch("coach.storage.settings") as mock_settings:
        mock_settings.data_dir = tmp_path
        storage.save_daily_card(card)
        loaded = storage.load_daily_card(card.date)
    assert loaded is not None
    assert loaded.motivation_note == "Go!"
    assert loaded.actions[0].domain == Domain.GUITAR


def test_load_recent_checkins_empty(tmp_path):
    with patch("coach.storage.settings") as mock_settings:
        mock_settings.data_dir = tmp_path
        result = storage.load_recent_checkins(7)
    assert result == []


def test_save_and_load_milestone_card(tmp_path):
    from coach.models import MilestoneCard
    card = MilestoneCard(
        date=datetime(2026, 4, 10),
        domain=Domain.GUITAR,
        achievement="10 sessions done",
        next_challenge="Learn barre chords",
    )
    with patch("coach.storage.settings") as mock_settings:
        mock_settings.data_dir = tmp_path
        storage.save_milestone_card(card)
        loaded = storage.load_milestone_card(card.date, card.domain)
    assert loaded is not None
    assert loaded.achievement == "10 sessions done"
