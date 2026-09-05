import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/inference",
    tags=["Inference"],
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
def inference_status():
    return {
        "service": "Sentronix Inference Engine",
        "status": "READY",
        "ai": "running",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/status")
def get_inference_status():
    return {
        "status": "running",
        "model": "sentronix-detector-v1",
        "engine": "YOLO",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/latest")
def get_latest_inference():
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
                "message": "No inference results found",
            }

        return {
            "success": True,
            "inference": dict(row),
        }

    finally:
        connection.close()


@router.get("/recent")
def get_recent_inferences(
    limit: int = 50,
):
    limit = max(
        1,
        min(
            limit,
            500,
        ),
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

        results = [dict(row) for row in rows]

        return {
            "count": len(results),
            "results": results,
        }

    finally:
        connection.close()


@router.get("/camera/{camera_id}")
def get_camera_inferences(
    camera_id: str,
    limit: int = 50,
):
    limit = max(
        1,
        min(
            limit,
            500,
        ),
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

        results = [dict(row) for row in rows]

        return {
            "camera": camera_id,
            "count": len(results),
            "results": results,
        }

    finally:
        connection.close()


@router.get("/object/{object_name}")
def get_object_inferences(
    object_name: str,
    limit: int = 50,
):
    limit = max(
        1,
        min(
            limit,
            500,
        ),
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

        results = [dict(row) for row in rows]

        return {
            "object": object_name,
            "count": len(results),
            "results": results,
        }

    finally:
        connection.close()


@router.get("/statistics")
def inference_statistics():
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

        unique_objects = connection.execute(
            """
            SELECT COUNT(
                DISTINCT object
            )
            FROM detections
            """
        ).fetchone()[0]

        unique_cameras = connection.execute(
            """
            SELECT COUNT(
                DISTINCT camera
            )
            FROM detections
            """
        ).fetchone()[0]

        return {
            "total_inferences": total,
            "unique_objects": unique_objects,
            "unique_cameras": unique_cameras,
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
