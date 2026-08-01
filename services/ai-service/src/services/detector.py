from __future__ import annotations

from typing import Any

from src.detector.detector import (
    detector as detection_engine,
)


class DetectorService:
    """
    Detection service wrapper.
    """

    def detect(
        self,
        image,
        confidence: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Run object detection.
        """

        return detection_engine.detect(
            image,
            confidence,
        )

    def detect_batch(
        self,
        images: list,
        confidence: float | None = None,
    ) -> list[list[dict]]:
        """
        Run batch detection.
        """

        return detection_engine.detect_batch(
            images,
            confidence,
        )


detector = DetectorService()
