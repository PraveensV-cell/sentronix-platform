from pathlib import Path

from src.core.config import settings
from src.core.logger import logger


async def startup():
    """
    Create required directories.
    """

    Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)

    Path(settings.RECORDING_DIR).mkdir(exist_ok=True)

    Path("logs").mkdir(exist_ok=True)

    logger.info("Camera Service Started")


async def shutdown():
    logger.info("Camera Service Stopped")
