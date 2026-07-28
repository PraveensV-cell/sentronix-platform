import threading
import time

from src.core.config import settings
from src.core.logger import logger


class HeartbeatService:
    """
    Background heartbeat service.
    """

    def __init__(self):
        self.running = False
        self.thread = None

    def start(self) -> None:
        """
        Start heartbeat thread.
        """

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
        )

        self.thread.start()

        logger.info("Heartbeat service started.")

    def stop(self) -> None:
        """
        Stop heartbeat thread.
        """

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2)

        logger.info("Heartbeat service stopped.")

    def _heartbeat_loop(self) -> None:
        """
        Background heartbeat loop.
        """

        while self.running:
            logger.info("Heartbeat sent.")

            # Future:
            # Send heartbeat to API Gateway
            # Send CPU/RAM usage
            # Send Camera status
            # Send Device metrics

            time.sleep(settings.HEARTBEAT_INTERVAL)
