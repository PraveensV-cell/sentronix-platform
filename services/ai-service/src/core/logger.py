from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


LOG_DIR = Path(
    "logs",
)

LOG_DIR.mkdir(
    exist_ok=True,
)


logger.remove()


logger.add(
    sys.stdout,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
    ),
)


logger.add(
    LOG_DIR / "ai_service.log",
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)


__all__ = [
    "logger",
]
