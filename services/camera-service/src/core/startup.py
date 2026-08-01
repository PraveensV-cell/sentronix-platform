from pathlib import Path

from src.core.config import settings
from src.core.logger import logger
from src.services.camera_connection_manager import (
    camera_connection_manager,
)


async def startup():
    """
    Create required directories.
    """

    Path(settings.UPLOAD_DIR).mkdir(
        exist_ok=True,
    )

    Path(settings.RECORDING_DIR).mkdir(
        exist_ok=True,
    )

    Path("logs").mkdir(
        exist_ok=True,
    )

    logger.info("Camera Service Started")


async def shutdown():
    """
    Shutdown Camera Service.
    """

    camera_connection_manager.cleanup()

    logger.info("Camera Service Stopped")
