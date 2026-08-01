from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from src.core.logger import logger
from src.detector.detector import (
    detector,
)
from src.detector.tracker import (
    tracker,
)
from src.services.publisher_service import (
    publisher_service,
)
from src.services.tracking_service import (
    tracking_service,
)


class FrameConsumer:
    """
    Processes incoming camera frames.
    """

    async def process(
        self,
        frame_bytes: bytes,
        camera_id: int = 0,
    ) -> dict[str, Any]:
        """
        Decode frame and run AI detection.
        """

        try:
            array = np.frombuffer(
                frame_bytes,
                dtype=np.uint8,
            )

            frame = cv2.imdecode(
                array,
                cv2.IMREAD_COLOR,
            )

            if frame is None:
                return {
                    "success": False,
                    "message": "Invalid frame.",
                }

            detections = detector.detect(
                frame,
            )

            tracked = tracker.update(
                detections,
            )

            tracking_service.update(
                tracked,
            )

            if tracked:
                await publisher_service.publish_detection(
                    camera_id=camera_id,
                    detections=tracked,
                )

            return {
                "success": True,
                "camera_id": camera_id,
                "detections": tracked,
                "total_objects": len(
                    tracked,
                ),
            }

        except Exception as error:
            logger.error(
                f"Frame processing failed: {error}",
            )

            return {
                "success": False,
                "message": str(error),
            }


frame_consumer = FrameConsumer()
