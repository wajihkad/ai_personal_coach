from __future__ import annotations

# Todoist integration — Level 3.
# Guarded by enable_todoist feature flag.

import logging

from coach.config import settings
from coach.models import DailyCard

logger = logging.getLogger(__name__)


def create_tasks(card: DailyCard) -> None:
    if not settings.enable_todoist:
        return
    # TODO: implement Todoist API calls
    logger.info("Todoist integration not yet implemented.")
