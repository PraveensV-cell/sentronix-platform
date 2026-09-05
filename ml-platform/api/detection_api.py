import sqlite3
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/detections",
    tags=["Detections"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


@router.get("")
def get_detections(
    limit: int = 100,
):
    limit = max(
        1,
        min(limit, 500),
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        detections = [dict(row) for row in rows]

        return {
            "count": len(detections),
            "detections": detections,
        }

    finally:
        connection.close()


@router.get("/latest")
def get_latest_detection():
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM detections
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return {
                "success": False,
                "detection": None,
            }

        return {
            "success": True,
            "detection": dict(row),
        }

    finally:
        connection.close()


@router.get("/camera/{camera_id}")
def get_camera_detections(
    camera_id: str,
    limit: int = 100,
):
    limit = max(
        1,
        min(limit, 500),
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM detections
            WHERE camera = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                camera_id,
                limit,
            ),
        ).fetchall()

        detections = [dict(row) for row in rows]

        return {
            "camera": camera_id,
            "count": len(detections),
            "detections": detections,
        }

    finally:
        connection.close()


@router.get("/object/{object_name}")
def get_object_detections(
    object_name: str,
    limit: int = 100,
):
    limit = max(
        1,
        min(limit, 500),
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM detections
            WHERE LOWER(object) = LOWER(?)
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                object_name,
                limit,
            ),
        ).fetchall()

        detections = [dict(row) for row in rows]

        return {
            "object": object_name,
            "count": len(detections),
            "detections": detections,
        }

    finally:
        connection.close()


@router.get("/statistics")
def get_detection_statistics():
    connection = get_connection()

    try:
        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM detections
            """
        ).fetchone()[0]

        average_confidence = connection.execute(
            """
            SELECT AVG(confidence)
            FROM detections
            """
        ).fetchone()[0]

        cameras = connection.execute(
            """
            SELECT COUNT(DISTINCT camera)
            FROM detections
            """
        ).fetchone()[0]

        objects = connection.execute(
            """
            SELECT COUNT(DISTINCT object)
            FROM detections
            """
        ).fetchone()[0]

        return {
            "total": total,
            "cameras": cameras,
            "objects": objects,
            "average_confidence": (
                round(
                    average_confidence,
                    3,
                )
                if average_confidence is not None
                else 0
            ),
        }

    finally:
        connection.close()
