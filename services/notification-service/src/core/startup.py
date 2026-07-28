from src.core.logger import logger


def startup():

    logger.info("Initializing Notification Service...")

    logger.success("Notification Service Started Successfully.")


def shutdown():

    logger.info("Stopping Notification Service...")

    logger.success("Notification Service Shutdown Complete.")
