import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "sentronix.db"

CAMERA_ID = "TEST-CAM-01"


def seed_database():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM detections
        WHERE camera_id = ?
        """,
        (CAMERA_ID,),
    )

    cursor.execute(
        """
        DELETE FROM cameras
        WHERE camera_name = ?
        """,
        (CAMERA_ID,),
    )

    cursor.execute(
        """
        DELETE FROM alerts
        WHERE status = 'TEST'
        """
    )

    cursor.execute(
        """
        INSERT INTO cameras (
            camera_name,
            location,
            status
        )
        VALUES (?, ?, ?)
        """,
        (
            CAMERA_ID,
            "Main Entrance",
            "online",
        ),
    )

    timestamp = datetime.now().isoformat(timespec="seconds")

    detections = [
        (
            timestamp,
            CAMERA_ID,
            "person",
            0.97,
            "[120,80,260,360]",
        ),
        (
            timestamp,
            CAMERA_ID,
            "vehicle",
            0.91,
            "[300,120,620,410]",
        ),
        (
            timestamp,
            CAMERA_ID,
            "person",
            0.89,
            "[700,100,820,350]",
        ),
    ]

    cursor.executemany(
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
        detections,
    )

    alerts = [
        (
            timestamp,
            "person",
            "HIGH",
            0.97,
            "TEST",
        ),
        (
            timestamp,
            "vehicle",
            "CRITICAL",
            0.91,
            "TEST",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO alerts (
            timestamp,
            object,
            priority,
            confidence,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        alerts,
    )

    connection.commit()

    cameras = cursor.execute("SELECT * FROM cameras").fetchall()

    detections = cursor.execute("SELECT * FROM detections").fetchall()

    alerts = cursor.execute("SELECT * FROM alerts").fetchall()

    connection.close()

    print("Sentronix test data inserted successfully")

    print("CAMERAS:")
    for row in cameras:
        print(row)

    print("DETECTIONS:")
    for row in detections:
        print(row)

    print("ALERTS:")
    for row in alerts:
        print(row)


if __name__ == "__main__":
    seed_database()
