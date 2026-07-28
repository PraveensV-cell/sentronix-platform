import cv2

from src.core.config import settings
from src.detector.model_loader import model_loader


class LiveDetectionService:
    """
    Real-time webcam / RTSP detection.
    """

    def __init__(self):
        self.model = model_loader.get_model()

    def start(self, source=0):
        """
        Start live detection.
        source:
            0 -> Webcam
            RTSP URL -> IP Camera
        """

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            return {
                "success": False,
                "message": "Unable to open camera.",
            }

        while True:
            success, frame = cap.read()

            if not success:
                break

            results = self.model(
                frame,
                conf=settings.CONFIDENCE_THRESHOLD,
            )

            annotated = results[0].plot()

            cv2.imshow(
                "Sentronix Live Detection",
                annotated,
            )

            key = cv2.waitKey(1)

            if key == ord("q"):
                break

        cap.release()

        cv2.destroyAllWindows()

        return {
            "success": True,
            "message": "Live detection stopped.",
        }
