from pathlib import Path

from ultralytics.engine.results import Results

from src.core.config import settings
from src.detector.model_loader import model_loader
from src.utils.image import ImageUtils


class DetectionService:
    """
    Performs YOLO object detection.
    """

    def __init__(self):
        self.model = model_loader.get_model()

    def detect_image(self, image_path: str):
        """
        Detect objects and save annotated image.
        """

        results = self.model(
            image_path,
            conf=settings.CONFIDENCE_THRESHOLD,
        )

        detections = []

        saved_image = None

        for result in results:
            detections.extend(self._parse_result(result))

            if settings.SAVE_RESULTS:
                ImageUtils.ensure_output_directory()

                filename = Path(image_path).name

                save_path = ImageUtils.output_path(filename)

                result.save(filename=save_path)

                saved_image = save_path

        return {
            "detections": detections,
            "annotated_image": saved_image,
        }

    def _parse_result(
        self,
        result: Results,
    ):

        output = []

        for box in result.boxes:
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist(),
            )

            confidence = float(box.conf[0])

            class_id = int(box.cls[0])

            label = result.names[class_id]

            output.append(
                {
                    "label": label,
                    "confidence": round(confidence, 4),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                }
            )

        return output
