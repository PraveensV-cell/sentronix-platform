import logging

logger = logging.getLogger("sentronix")


async def startup():
    """
    Executed when the application starts.
    """

    logger.info("=" * 60)
    logger.info("Starting SENTRONIX API Gateway")
    logger.info("Loading configuration...")
    logger.info("Initializing services...")
    logger.info("API Gateway Ready")
    logger.info("=" * 60)


async def shutdown():
    """
    Executed when the application stops.
    """

    logger.info("=" * 60)
    logger.info("Stopping SENTRONIX API Gateway")
    logger.info("Cleaning resources...")
    logger.info("Shutdown Complete")
    logger.info("=" * 60)
