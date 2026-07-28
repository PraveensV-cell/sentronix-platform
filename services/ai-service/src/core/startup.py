from src.core.logger import logger
from src.detector.model_loader import model_loader


async def startup():
    """
    Application startup.
    """

    logger.info("====================================")
    logger.info("Starting AI Detection Service")
    logger.info("====================================")

    model_loader.load_model()

    logger.success("Startup Complete")


async def shutdown():
    """
    Application shutdown.
    """

    logger.info("====================================")
    logger.info("Stopping AI Detection Service")
    logger.info("====================================")
