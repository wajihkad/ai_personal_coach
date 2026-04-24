from __future__ import annotations

from datetime import datetime

from coach.models import Action, CheckIn, DailyCard, DomainProfile, Level, MilestoneCard, ProfileCard, Status, WeeklyCard


def test_status_defaults_to_pending():
    action = Action(domain="guitar", description="Practice scales", duration_minutes=20)
    assert action.status == Status.PENDING
    assert action.feedback is None


def test_domain_is_plain_string():
    dp = DomainProfile(domain="running", level=Level.BEGINNER, goal="Run 5k", hours_per_week=2.0)
    assert dp.domain == "running"


def test_daily_card_structure():
    actions = [
        Action(domain="guitar", description="Scales", duration_minutes=20),
        Action(domain="chess", description="Puzzles", duration_minutes=15),
    ]
    card = DailyCard(date=datetime.now(), actions=actions, motivation_note="Keep it up!")
    assert len(card.actions) == 2
    assert card.generated_by_agent is True


def test_weekly_card_structure():
    card = WeeklyCard(
        week_start=datetime(2026, 4, 7),
        week_end=datetime(2026, 4, 13),
        domain_summaries={"guitar": "Good week"},
        completion_rate={"guitar": 0.8},
        highlight="Finished a full song",
        next_week_focus=[],
    )
    assert card.completion_rate["guitar"] == 0.8


def test_milestone_card_structure():
    card = MilestoneCard(
        date=datetime.now(),
        domain="guitar",
        achievement="10 sessions completed",
        next_challenge="Learn a new chord progression",
    )
    assert card.domain == "guitar"


def test_checkin_energy_level(sample_checkin):
    assert 1 <= sample_checkin.energy_level <= 5
