from __future__ import annotations

# Google Calendar integration — Level 3.
# Guarded by enable_calendar feature flag.

import logging

from coach.config import settings
from coach.models import DailyCard

logger = logging.getLogger(__name__)


def create_calendar_events(card: DailyCard) -> None:
    if not settings.enable_calendar:
        return
    # TODO: implement Google Calendar API calls
    logger.info("Calendar integration not yet implemented.")
