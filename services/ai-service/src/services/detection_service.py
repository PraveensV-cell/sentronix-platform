from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.config import settings
from src.core.logger import logger
from src.detector.detector import detector
from src.detector.model_loader import model_loader
from src.utils.image import ImageUtils


class DetectionService:
    """
    Performs YOLO object detection.
    """

    def detect_image(
        self,
        image_path: str,
    ) -> dict[str, Any]:
        """
        Detect objects from image.
        """

        try:
            detections = detector.detect(
                image_path,
                settings.CONFIDENCE_THRESHOLD,
            )

            annotated_image = None

            if settings.SAVE_RESULTS:
                ImageUtils.ensure_output_directory()

                filename = Path(
                    image_path,
                ).name

                save_path = ImageUtils.output_path(
                    filename,
                )

                model = model_loader.get_model()

                results = model.predict(
                    source=image_path,
                    conf=settings.CONFIDENCE_THRESHOLD,
                    verbose=False,
                )

                for result in results:
                    result.save(
                        filename=save_path,
                    )

                annotated_image = save_path

            return {
                "success": True,
                "detections": detections,
                "annotated_image": annotated_image,
                "total_objects": len(detections),
            }

        except Exception as error:
            logger.error(
                f"Detection failed: {error}",
            )

            return {
                "success": False,
                "detections": [],
                "annotated_image": None,
                "total_objects": 0,
            }

    async def submit_detection_task(
        self,
        image_path: str,
        camera_id: int = 0,
    ):
        """
        Add detection task to background worker.
        """

        # Local import prevents circular import
        from src.workers.detection_worker import (
            detection_worker,
        )

        await detection_worker.add_task(
            {
                "image": image_path,
                "camera_id": camera_id,
            }
        )

        return {
            "success": True,
            "message": "Detection task queued.",
        }

    def detect_batch(
        self,
        images: list[str],
    ) -> list[dict[str, Any]]:
        """
        Detect objects from multiple images.
        """

        results = []

        for image in images:
            results.append(
                self.detect_image(
                    image,
                )
            )

        return results


detection_service = DetectionService()
