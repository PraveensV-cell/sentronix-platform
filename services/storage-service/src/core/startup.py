from pathlib import Path

from src.core.config import settings
from src.core.logger import logger


def startup():

    Path(settings.STORAGE_DIR).mkdir(exist_ok=True)

    Path(settings.IMAGE_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(settings.VIDEO_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(settings.SNAPSHOT_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(settings.TEMP_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info("Initializing Storage Service...")

    logger.success("Storage Service Started Successfully.")


def shutdown():

    logger.info("Stopping Storage Service...")

    logger.success("Storage Service Shutdown Complete.")
