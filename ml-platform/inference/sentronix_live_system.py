import time
from pathlib import Path
from typing import cast

import cv2
from inference.alert_engine import check_detection, save_alert
from inference.event_logger import create_event, save_event
from ultralytics import YOLO
from ultralytics.engine.results import Results

PROJECT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_DIR
    / "runs"
    / "detect"
    / "models"
    / "sentronix-detector-v1"
    / "detector-v1"
    / "weights"
    / "best.pt"
)

CAMERA_SOURCE = 0
CONFIDENCE = 0.5


def load_model():
    if not MODEL_PATH.exists():
        print("Model not found:")
        print(MODEL_PATH)
        return None

    return YOLO(str(MODEL_PATH))


def process_results(results: Results, frame_id: int):
    detections = []

    if results.boxes is None:
        return detections

    for box in results.boxes:
        class_id = int(box.cls.item())
        confidence = float(box.conf.item())
        class_name = results.names[class_id]
        coordinates = box.xyxy[0].tolist()

        detection = {
            "name": class_name,
            "confidence": confidence,
            "bbox": coordinates,
        }

        detections.append(detection)

        event = create_event(
            camera="camera_01",
            frame_id=frame_id,
            class_name=class_name,
            confidence=confidence,
            bbox=coordinates,
        )

        save_event(event)

        alert = check_detection(
            class_name,
            confidence,
        )

        if alert:
            save_alert(alert)
            print(f"ALERT: {class_name} ({confidence:.2f})")

    return detections


def run_system():
    print("Starting Sentronix AI Security System")
    print(f"Model: {MODEL_PATH}")

    model = load_model()

    if model is None:
        return

    camera = cv2.VideoCapture(CAMERA_SOURCE)

    if not camera.isOpened():
        print("Camera unavailable")
        return

    frame_id = 0
    previous_time = time.time()

    print("Camera started")
    print("Press Q to stop")

    while True:
        success, frame = camera.read()

        if not success:
            print("Unable to read camera frame")
            break

        predictions = cast(
            list[Results],
            model(
                frame,
                conf=CONFIDENCE,
                verbose=False,
            ),
        )

        results = predictions[0]

        process_results(
            results,
            frame_id,
        )

        output = results.plot()

        current_time = time.time()
        elapsed = current_time - previous_time

        fps = 0.0

        if elapsed > 0:
            fps = 1.0 / elapsed

        previous_time = current_time

        cv2.putText(
            output,
            f"FPS: {fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            output,
            "SENTRONIX AI",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        cv2.imshow(
            "Sentronix AI Security",
            output,
        )

        frame_id += 1

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("Sentronix AI Security System stopped")


def main():
    run_system()


if __name__ == "__main__":
    main()
