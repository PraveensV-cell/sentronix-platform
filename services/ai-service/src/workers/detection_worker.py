from __future__ import annotations

from asyncio import Queue
from typing import Any

from src.core.logger import logger
from src.services.publisher_service import (
    publisher_service,
)


class DetectionWorker:
    """
    Background AI detection worker.
    """

    def __init__(self):
        self.queue: Queue[dict[str, Any]] = Queue()

        self.running = False

    async def add_task(
        self,
        task: dict[str, Any],
    ):
        """
        Add detection task.
        """

        await self.queue.put(
            task,
        )

    async def start(
        self,
    ):
        """
        Start background worker.
        """

        self.running = True

        logger.info(
            "Detection worker started.",
        )

        while self.running:
            try:
                task = await self.queue.get()

                # Local import avoids circular dependency
                from src.services.detection_service import (
                    detection_service,
                )

                result = detection_service.detect_image(
                    task["image"],
                )

                if result.get(
                    "success",
                    False,
                ):
                    await publisher_service.publish_detection(
                        camera_id=task.get(
                            "camera_id",
                            0,
                        ),
                        detections=result.get(
                            "detections",
                            [],
                        ),
                    )

            except Exception as error:
                logger.error(
                    f"Worker error: {error}",
                )

            finally:
                self.queue.task_done()

    async def stop(
        self,
    ):
        """
        Stop background worker.
        """

        self.running = False

        logger.info(
            "Detection worker stopped.",
        )

    def pending_tasks(
        self,
    ) -> int:
        """
        Get queued task count.
        """

        return self.queue.qsize()


detection_worker = DetectionWorker()
