from __future__ import annotations

from datetime import datetime

import pytest

from coach.models import Action, CheckIn, DomainProfile, Level, ProfileCard, Status


@pytest.fixture()
def sample_profile() -> ProfileCard:
    return ProfileCard(
        user_name="Alex",
        domains=[
            DomainProfile(domain="guitar", level=Level.BEGINNER, goal="Learn fingerpicking", hours_per_week=3.0),
            DomainProfile(domain="chess", level=Level.BEGINNER, goal="Reach 1000 ELO", hours_per_week=2.0),
        ],
        available_days=["monday", "wednesday", "friday"],
        preferred_session_length=30,
        learning_style="hands-on",
    )


@pytest.fixture()
def sample_checkin() -> CheckIn:
    return CheckIn(
        date=datetime(2026, 4, 10),
        completed_actions=[
            Action(
                domain="guitar",
                description="Practiced C major scale",
                duration_minutes=20,
                status=Status.DONE,
            )
        ],
        energy_level=4,
        free_text="Good session today, feeling motivated.",
    )
