from __future__ import annotations

# Telegram bot integration — Level 3.
# Guarded by enable_telegram feature flag.

import logging

from coach.config import settings
from coach.models import DailyCard

logger = logging.getLogger(__name__)


def send_daily_briefing(card: DailyCard) -> None:
    if not settings.enable_telegram:
        return
    # TODO: implement Telegram Bot API calls
    logger.info("Telegram integration not yet implemented.")


def send_evening_nudge() -> None:
    if not settings.enable_telegram:
        return
    # TODO: implement Telegram nudge
    logger.info("Telegram nudge not yet implemented.")
