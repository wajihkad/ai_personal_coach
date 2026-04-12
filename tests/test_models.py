from __future__ import annotations

from datetime import datetime

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
    WeeklyCard,
)


def test_domain_enum_values():
    assert Domain.GUITAR.value == "guitar"
    assert Domain.CHESS.value == "chess"
    assert Domain.CODING.value == "coding"


def test_status_defaults_to_pending():
    action = Action(domain=Domain.GUITAR, description="Practice scales", duration_minutes=20)
    assert action.status == Status.PENDING
    assert action.feedback is None


def test_daily_card_structure(sample_profile):
    actions = [
        Action(domain=Domain.GUITAR, description="Scales", duration_minutes=20),
        Action(domain=Domain.CHESS, description="Puzzles", duration_minutes=15),
    ]
    card = DailyCard(date=datetime.now(), actions=actions, motivation_note="Keep it up!")
    assert len(card.actions) == 2
    assert card.generated_by_agent is True


def test_weekly_card_structure():
    card = WeeklyCard(
        week_start=datetime(2026, 4, 7),
        week_end=datetime(2026, 4, 13),
        domain_summaries={Domain.GUITAR: "Good week"},
        completion_rate={Domain.GUITAR: 0.8},
        highlight="Finished a full song",
        next_week_focus=[],
    )
    assert card.completion_rate[Domain.GUITAR] == 0.8


def test_milestone_card_structure():
    card = MilestoneCard(
        date=datetime.now(),
        domain=Domain.GUITAR,
        achievement="10 sessions completed",
        next_challenge="Learn a new chord progression",
    )
    assert card.domain == Domain.GUITAR


def test_checkin_energy_level(sample_checkin):
    assert 1 <= sample_checkin.energy_level <= 5
