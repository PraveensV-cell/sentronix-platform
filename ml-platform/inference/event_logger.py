import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"


def get_connection():
    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


def create_event(
    camera,
    frame_id,
    class_name,
    confidence,
    bbox,
):
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera": camera,
        "frame": frame_id,
        "object": class_name,
        "confidence": round(
            confidence,
            3,
        ),
        "bbox": bbox,
    }


def save_event(event):
    camera = event["camera"]

    if isinstance(camera, int):
        camera_id = camera
    else:
        try:
            camera_id = int(str(camera).replace("camera_", "").replace("CAMERA_", ""))
        except ValueError:
            camera_id = None

    if camera_id is None:
        return

    connection = get_connection()

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
                event["timestamp"],
                camera_id,
                event["object"],
                event["confidence"],
                str(event["bbox"]),
            ),
        )

        connection.commit()

    finally:
        connection.close()


def main():
    event = create_event(
        camera="camera_01",
        frame_id=100,
        class_name="person",
        confidence=0.91,
        bbox=[
            100,
            120,
            250,
            400,
        ],
    )

    save_event(event)

    print("Detection event saved to database")


if __name__ == "__main__":
    main()
