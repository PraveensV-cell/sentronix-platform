import threading
import time

from sqlalchemy.orm import Session

from src.ai.detector import AIEngine
from src.alerts.alert_engine import AlertEngine
from src.database.session import SessionLocal
from src.schemas.detection import DetectionCreate
from src.services.detection import DetectionService
from src.streaming.manager import stream_manager


class DetectionWorker:
    """
    Background worker that continuously performs
    AI inference on active camera streams.
    """

    def __init__(self):
        self.engine = AIEngine()
        self.running = False
        self.thread: threading.Thread | None = None

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.run,
            daemon=True,
        )

        self.thread.start()

    def stop(self):
        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2)

    def run(self):
        while self.running:
            for camera_id, stream in list(stream_manager.streams.items()):
                frame = stream.get_raw_frame()

                if frame is None:
                    continue

                try:
                    detections = self.engine.detect(frame)

                    annotated_frame = self.engine.draw_detections(
                        frame.copy(),
                        detections,
                    )

                    # Update stream
                    stream.frame = annotated_frame

                    db: Session = SessionLocal()

                    detection_service = DetectionService(db)

                    alert_engine = AlertEngine(db)

                    try:
                        for detection in detections:
                            saved_detection = detection_service.create_detection(
                                DetectionCreate(
                                    camera_id=camera_id,
                                    label=detection.label,
                                    confidence=detection.confidence,
                                    x1=detection.x1,
                                    y1=detection.y1,
                                    x2=detection.x2,
                                    y2=detection.y2,
                                )
                            )

                            alert_engine.process_detection(saved_detection)

                    finally:
                        db.close()

                except Exception as exc:
                    print(f"[DetectionWorker] Camera {camera_id}: {exc}")

            time.sleep(1)
