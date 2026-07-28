from src.core.logger import logger


def startup() -> None:
    logger.info("Initializing Event Service...")
    logger.success("Event Service Started Successfully.")


def shutdown() -> None:
    logger.info("Stopping Event Service...")
    logger.success("Event Service Shutdown Complete.")
