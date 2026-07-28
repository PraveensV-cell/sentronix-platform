from loguru import logger
import sys

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
)

logger.add(
    "logs/camera_service.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
)

__all__ = ["logger"]
