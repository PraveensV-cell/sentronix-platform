from pathlib import Path

from loguru import logger

from src.core.config import settings


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sink=lambda msg: print(msg, end=""),
    level=settings.LOG_LEVEL,
    colorize=True,
)

logger.add(
    LOG_DIR / "device_service.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level=settings.LOG_LEVEL,
    enqueue=True,
)

__all__ = ["logger"]
