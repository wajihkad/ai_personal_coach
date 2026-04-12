from __future__ import annotations

# Lichess integration — Level 3.
# Fetches the daily puzzle for chess domain actions.
# No API key required (public endpoint).
# Guarded by enable_lichess feature flag.

import logging
from typing import Optional

from coach.config import settings

logger = logging.getLogger(__name__)


def fetch_daily_puzzle() -> Optional[str]:
    """Return a URL to today's Lichess daily puzzle, or None if disabled/unavailable."""
    if not settings.enable_lichess:
        return None
    # TODO: implement Lichess API call
    logger.info("Lichess integration not yet implemented.")
    return None
