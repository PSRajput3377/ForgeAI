"""Loguru-based logging setup."""

import sys

from loguru import logger

from app.config import settings


def configure_logging() -> None:
    """Configure Loguru with a single stderr sink at the configured level."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        backtrace=settings.environment == "development",
        diagnose=settings.environment == "development",
    )
