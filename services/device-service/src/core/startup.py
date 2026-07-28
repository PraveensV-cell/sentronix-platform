from src.core.logger import logger
from src.services.heartbeat_service import HeartbeatService


heartbeat_service = HeartbeatService()


def startup() -> None:
    """
    Initialize the Device Service.
    """

    logger.info("Initializing Device Service...")

    heartbeat_service.start()

    logger.success("Device Service started successfully.")


def shutdown() -> None:
    """
    Shutdown the Device Service.
    """

    logger.info("Stopping Device Service...")

    heartbeat_service.stop()

    logger.success("Device Service stopped successfully.")
