from __future__ import annotations

from src.core.logger import logger
from src.detector.model_loader import (
    model_loader,
)


async def startup():
    """
    Application startup.
    """

    logger.info("====================================")

    logger.info("Starting AI Detection Service")

    logger.info("====================================")

    try:
        model_loader.load_model()

        logger.success("YOLO model loaded successfully.")

    except Exception as error:
        logger.error(f"Model loading failed: {error}")

        raise error

    model_loader.unload_models()

    logger.success("Shutdown Complete")


async def shutdown():
    """
    Application shutdown.
    """

    logger.info("====================================")

    logger.info("Stopping AI Detection Service")

    logger.info("====================================")

    logger.success("Shutdown Complete")
