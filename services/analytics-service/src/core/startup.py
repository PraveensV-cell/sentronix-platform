from src.core.logger import logger


def startup():

    logger.info("Initializing Analytics Service...")

    logger.success("Analytics Service Started Successfully.")


def shutdown():

    logger.info("Stopping Analytics Service...")

    logger.success("Analytics Service Shutdown Complete.")
