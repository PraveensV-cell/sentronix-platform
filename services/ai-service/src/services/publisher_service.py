from __future__ import annotations

from datetime import datetime
from typing import Any

from src.core.logger import logger
from src.services.event_client import (
    event_client,
)


class PublisherService:
    """
    Publishes AI detection events.
    """

    async def publish_detection(
        self,
        camera_id: int,
        detections: list[dict[str, Any]],
    ) -> bool:
        """
        Publish detection result to Event Service.
        """

        if not detections:
            return False

        try:
            await event_client.publish_detection(
                camera_id=camera_id,
                detections=[
                    {
                        **detection,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    for detection in detections
                ],
            )

            logger.info(
                "AI detection event published successfully.",
            )

            return True

        except Exception as error:
            logger.error(
                f"Detection publish failed: {error}",
            )

            return False

    async def publish_batch(
        self,
        events: list[dict[str, Any]],
    ) -> list[bool]:
        """
        Publish multiple detection events.
        """

        results = []

        for event in events:
            result = await self.publish_detection(
                camera_id=event.get(
                    "camera_id",
                    0,
                ),
                detections=event.get(
                    "detections",
                    [],
                ),
            )

            results.append(
                result,
            )

        return results


publisher_service = PublisherService()
