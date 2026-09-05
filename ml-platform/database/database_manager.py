import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "sentronix.db"


def create_database():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            camera_id TEXT,
            object TEXT,
            confidence REAL,
            bbox TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            object TEXT,
            priority TEXT,
            confidence REAL,
            status TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_name TEXT,
            location TEXT,
            status TEXT
        )
        """
    )

    connection.commit()
    connection.close()

    print("Database created")


def save_detection(
    camera_id,
    object_name,
    confidence,
    bbox,
):
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            camera_id,
            object_name,
            confidence,
            str(bbox),
        ),
    )

    connection.commit()
    connection.close()


def save_alert(
    object_name,
    priority,
    confidence,
):
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
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
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            object_name,
            priority,
            confidence,
            "ACTIVE",
        ),
    )

    connection.commit()
    connection.close()


def main():
    print("Sentronix Database Manager")

    create_database()

    save_detection(
        "camera_01",
        "person",
        0.91,
        [100, 120, 250, 400],
    )

    save_alert(
        "fire",
        "CRITICAL",
        0.95,
    )

    print("Test records inserted")


if __name__ == "__main__":
    main()
