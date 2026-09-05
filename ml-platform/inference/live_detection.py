import sqlite3
from pathlib import Path

from inference.alert_engine import check_detection, save_alert
from inference.event_logger import create_event, save_event

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"


def save_detection_to_database(
    camera_id,
    timestamp,
    class_name,
    confidence,
    bbox,
):
    connection = sqlite3.connect(str(DATABASE_PATH))

    try:
        connection.execute(
            """
            INSERT INTO detections (
                timestamp,
                camera_id,
                object,
                confidence,
                bbox
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                camera_id,
                class_name,
                confidence,
                str(bbox),
            ),
        )

        connection.commit()

    finally:
        connection.close()


def process_detection(
    camera_id,
    frame_id,
    class_name,
    confidence,
    bbox,
):
    event = create_event(
        camera=f"camera_{camera_id:02d}",
        frame_id=frame_id,
        class_name=class_name,
        confidence=confidence,
        bbox=bbox,
    )

    save_event(event)

    save_detection_to_database(
        camera_id=camera_id,
        timestamp=event["timestamp"],
        class_name=class_name,
        confidence=confidence,
        bbox=bbox,
    )

    alert = check_detection(
        class_name,
        confidence,
    )

    if alert:
        alert["camera_id"] = camera_id
        save_alert(alert)

        return {
            "detection": event,
            "alert": alert,
        }

    return {
        "detection": event,
        "alert": None,
    }


def process_yolo_results(
    results,
    camera_id,
    frame_id,
):
    processed = []

    if results is None:
        return processed

    boxes = results.boxes

    if boxes is None:
        return processed

    for box in boxes:
        class_id = int(box.cls[0])

        confidence = float(box.conf[0])

        class_name = results.names[class_id]

        bbox = box.xyxy[0].tolist()

        result = process_detection(
            camera_id=camera_id,
            frame_id=frame_id,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox,
        )

        processed.append(result)

    return processed
