from __future__ import annotations

from typing import Any

from src.core.config import settings
from src.core.logger import logger
from src.detector.model_loader import (
    model_loader,
)


class Detector:
    """
    Handles YOLO object detection with filtering.
    """

    def __init__(self):
        self.model = model_loader.get_model()

    def detect(
        self,
        image,
        confidence: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Run object detection.
        """

        try:
            threshold = (
                confidence if confidence is not None else settings.CONFIDENCE_THRESHOLD
            )

            results = self.model.predict(
                source=image,
                conf=threshold,
                verbose=False,
            )

            detections = []

            for result in results:
                boxes = result.boxes  # type: ignore

                if boxes is None:
                    continue

                for box in boxes:  # type: ignore
                    class_id = int(
                        box.cls[0],  # type: ignore
                    )

                    score = float(
                        box.conf[0],  # type: ignore
                    )

                    class_name = self.model.names[class_id]

                    coordinates = box.xyxy[0].tolist()  # type: ignore

                    detection = {
                        "class_id": class_id,
                        "class_name": class_name,
                        "label": class_name,
                        "confidence": round(
                            score,
                            3,
                        ),
                        "bbox": coordinates,
                    }

                    if not self.filter_class(
                        detection,
                    ):
                        continue

                    if not self.filter_region(
                        detection,
                    ):
                        continue

                    detections.append(
                        detection,
                    )

            return detections

        except Exception as error:
            logger.error(
                f"Detection failed: {error}",
            )

            return []

    def filter_class(
        self,
        detection: dict,
    ) -> bool:
        """
        Filter unwanted classes.
        """

        if not settings.ENABLE_CLASS_FILTER:
            return True

        return detection["class_name"] in settings.ALLOWED_CLASSES

    def filter_region(
        self,
        detection: dict,
    ) -> bool:
        """
        Filter detections outside region.
        """

        if not settings.ENABLE_REGION_FILTER:
            return True

        x1, y1, x2, y2 = detection["bbox"]

        return (
            x1 >= settings.REGION_X1
            and y1 >= settings.REGION_Y1
            and x2 <= settings.REGION_X2
            and y2 <= settings.REGION_Y2
        )

    def detect_batch(
        self,
        images: list,
        confidence: float | None = None,
    ) -> list[list[dict]]:
        """
        Run detection on multiple images.
        """

        results = []

        for image in images:
            results.append(
                self.detect(
                    image,
                    confidence,
                )
            )

        return results


detector = Detector()
