from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from coach.models import Action, CheckIn, DailyCard, DomainProfile, Level, MilestoneCard, ProfileCard, Status, WeeklyCard
from coach import storage


@pytest.fixture(autouse=True)
def patch_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("coach.storage.settings", type("S", (), {"data_dir": tmp_path})())


def test_save_and_load_profile(sample_profile):
    storage.save_profile(sample_profile)
    loaded = storage.load_profile()
    assert loaded is not None
    assert loaded.user_name == sample_profile.user_name
    assert loaded.domains[0].domain == "guitar"


def test_load_missing_profile_returns_none():
    result = storage.load_profile()
    assert result is None


def test_save_and_load_checkin(sample_checkin):
    storage.save_checkin(sample_checkin)
    loaded = storage.load_checkin(sample_checkin.date)
    assert loaded is not None
    assert loaded.energy_level == sample_checkin.energy_level
    assert loaded.free_text == sample_checkin.free_text


def test_save_and_load_daily_card():
    actions = [Action(domain="guitar", description="Scales", duration_minutes=20)]
    card = DailyCard(date=datetime(2026, 4, 10), actions=actions, motivation_note="Go!")
    storage.save_daily_card(card)
    loaded = storage.load_daily_card(card.date)
    assert loaded is not None
    assert loaded.motivation_note == "Go!"
    assert loaded.actions[0].domain == "guitar"


def test_load_recent_checkins_empty():
    result = storage.load_recent_checkins(7)
    assert result == []


def test_save_and_load_milestone_card():
    card = MilestoneCard(
        date=datetime(2026, 4, 10),
        domain="guitar",
        achievement="10 sessions done",
        next_challenge="Learn barre chords",
    )
    storage.save_milestone_card(card)
    loaded = storage.load_milestone_card(card.date, card.domain)
    assert loaded is not None
    assert loaded.achievement == "10 sessions done"
