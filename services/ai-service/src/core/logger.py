from loguru import logger
import sys

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level}</level> | "
    "{message}",
)

logger.add(
    "logs/ai_service.log",
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
)

__all__ = ["logger"]
