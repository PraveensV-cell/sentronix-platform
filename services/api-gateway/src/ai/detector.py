import cv2

from src.ai.model_loader import ModelLoader
from src.ai.types import Detection


class AIEngine:
    """
    Generic AI detection engine.
    """

    def __init__(
        self,
        model="models/yolov8n.pt",
    ):
        self.model = ModelLoader.load_yolo(model)

    def detect(self, frame):

        results = self.model(frame)

        detections = []

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])

                confidence = float(box.conf[0])

                label = result.names[cls]

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0],
                )

                detections.append(
                    Detection(
                        label=label,
                        confidence=confidence,
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                    )
                )

        return detections

    def draw_detections(
        self,
        frame,
        detections,
    ):
        """
        Draw bounding boxes.
        """

        for detection in detections:
            cv2.rectangle(
                frame,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"{detection.label} {detection.confidence:.2f}",
                (detection.x1, detection.y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        return frame
