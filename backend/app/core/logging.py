"""Structured Logging Configuration for CareerMetricX."""

import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured console logging."""
    logger = logging.getLogger(settings.APP_NAME)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()
