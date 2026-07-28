from pathlib import Path

from loguru import logger

from src.core.config import settings

LOG_DIR = Path("logs")

LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sink=lambda msg: print(msg, end=""),
    colorize=True,
    level=settings.LOG_LEVEL,
)

logger.add(
    LOG_DIR / "notification_service.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    enqueue=True,
    level=settings.LOG_LEVEL,
)

__all__ = ["logger"]
