from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from src.core.config import settings


LOG_DIR = Path(
    "logs",
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


logger.remove()


logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
    ),
)


logger.add(
    LOG_DIR / "event_service.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    enqueue=True,
    level=settings.LOG_LEVEL,
    format=("{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"),
)


__all__ = [
    "logger",
]
