from __future__ import annotations

from typing import Any

from src.core.logger import logger
from src.detector.model_loader import (
    model_loader,
)


class InferenceEngine:
    """
    Handles YOLO inference operations.
    """

    def __init__(self):
        self.model = model_loader.get_model()

    def run(
        self,
        image,
        confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Run inference on single image.
        """

        try:
            results = self.model.predict(
                source=image,
                conf=confidence,
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

                    bbox = box.xyxy[0].tolist()  # type: ignore

                    class_name = self.model.names[class_id]

                    detections.append(
                        {
                            "class_id": class_id,
                            "class_name": class_name,
                            "label": class_name,
                            "confidence": round(
                                score,
                                3,
                            ),
                            "bbox": bbox,
                        }
                    )

            return detections

        except Exception as error:
            logger.error(
                f"Inference failed: {error}",
            )

            return []

    def run_batch(
        self,
        images: list,
        confidence: float = 0.5,
    ) -> list[list[dict]]:
        """
        Run inference on multiple images.
        """

        output = []

        for image in images:
            output.append(
                self.run(
                    image,
                    confidence,
                )
            )

        return output


inference_engine = InferenceEngine()
