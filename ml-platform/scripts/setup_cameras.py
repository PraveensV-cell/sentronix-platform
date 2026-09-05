import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"


CAMERAS = [
    {
        "id": 1,
        "name": "Camera 01",
        "location": "Main Entrance",
        "source": 0,
    },
    {
        "id": 2,
        "name": "Camera 02",
        "location": "Parking Area",
        "source": 1,
    },
    {
        "id": 3,
        "name": "Camera 03",
        "location": "Restricted Area",
        "source": 2,
    },
]


def setup_cameras():
    connection = sqlite3.connect(str(DATABASE_PATH))

    cursor = connection.cursor()

    columns = cursor.execute("PRAGMA table_info(cameras)").fetchall()

    column_names = [column[1] for column in columns]

    if "source" not in column_names:
        cursor.execute(
            """
            ALTER TABLE cameras
            ADD COLUMN source INTEGER
            """
        )

    for camera in CAMERAS:
        existing = cursor.execute(
            """
            SELECT id
            FROM cameras
            WHERE id = ?
            """,
            (camera["id"],),
        ).fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE cameras
                SET
                    camera_name = ?,
                    location = ?,
                    source = ?
                WHERE id = ?
                """,
                (
                    camera["name"],
                    camera["location"],
                    camera["source"],
                    camera["id"],
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO cameras (
                    id,
                    camera_name,
                    location,
                    status,
                    source
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    camera["id"],
                    camera["name"],
                    camera["location"],
                    "offline",
                    camera["source"],
                ),
            )

    connection.commit()

    rows = cursor.execute(
        """
        SELECT
            id,
            camera_name,
            location,
            status,
            source
        FROM cameras
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    print("Camera configuration:")

    for row in rows:
        print(row)


if __name__ == "__main__":
    setup_cameras()
