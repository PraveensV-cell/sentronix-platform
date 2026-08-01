from __future__ import annotations

import cv2

from src.core.config import settings
from src.core.logger import logger
from src.detector.inference import (
    inference_engine,
)
from src.detector.tracker import (
    tracker,
)
from src.services.tracking_service import (
    tracking_service,
)


class LiveDetectionService:
    """
    Handles real-time camera detection and tracking.
    """

    def __init__(self):
        self.active_streams = {}

    def process_frame(
        self,
        frame,
    ):
        """
        Run detection and tracking on frame.
        """

        detections = inference_engine.run(
            frame,
            settings.CONFIDENCE_THRESHOLD,
        )

        tracked_objects = tracker.update(
            detections,
        )

        tracking_service.update(
            tracked_objects,
        )

        return tracked_objects

    def start(
        self,
        source=0,
    ):
        """
        Start live detection.

        source:
            0 -> USB Camera
            RTSP URL -> IP Camera
        """

        capture = cv2.VideoCapture(
            source,
        )

        if not capture.isOpened():
            return {
                "success": False,
                "message": "Unable to open camera.",
            }

        stream_id = str(
            source,
        )

        self.active_streams[stream_id] = capture

        try:
            while capture.isOpened():
                success, frame = capture.read()

                if not success:
                    break

                detections = self.process_frame(
                    frame,
                )

                yield {
                    "frame": frame.copy(),
                    "detections": detections,
                }

        except Exception as error:
            logger.error(
                f"Live detection error: {error}",
            )

        finally:
            capture.release()

            self.active_streams.pop(
                stream_id,
                None,
            )

    def stop(
        self,
        source,
    ):
        """
        Stop live detection.
        """

        stream_id = str(
            source,
        )

        capture = self.active_streams.get(
            stream_id,
        )

        if capture:
            capture.release()

            self.active_streams.pop(
                stream_id,
                None,
            )

            return True

        return False

    def active_count(
        self,
    ) -> int:
        """
        Active detection streams.
        """

        return len(
            self.active_streams,
        )


live_detection_service = LiveDetectionService()
