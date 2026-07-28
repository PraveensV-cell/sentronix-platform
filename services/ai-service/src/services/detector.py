from src.detector.model_loader import model_loader


class DetectorService:
    """
    Detection service using the shared YOLO model.
    """

    def __init__(self):
        self.model = model_loader.get_model()

    def detect(self, image_path: str):

        results = self.model.predict(image_path)

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                detections.append(
                    {
                        "label": result.names[int(box.cls.item())],
                        "confidence": float(box.conf.item()),
                        "bbox": [float(x) for x in box.xyxy[0].tolist()],
                    }
                )

        return detections


detector = DetectorService()
