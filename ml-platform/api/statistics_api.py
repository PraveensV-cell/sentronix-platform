import sqlite3
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
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
def get_statistics():
    connection = get_connection()

    try:
        detections = connection.execute(
            """
            SELECT COUNT(*)
            FROM detections
            """
        ).fetchone()[0]

        alerts = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            """
        ).fetchone()[0]

        active_alerts = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(status) = 'ACTIVE'
            """
        ).fetchone()[0]

        critical_alerts = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(priority) = 'CRITICAL'
            """
        ).fetchone()[0]

        high_alerts = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(priority) = 'HIGH'
            """
        ).fetchone()[0]

        cameras = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            """
        ).fetchone()[0]

        online_cameras = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            WHERE UPPER(status) = 'ONLINE'
            """
        ).fetchone()[0]

        average_confidence = connection.execute(
            """
            SELECT AVG(confidence)
            FROM detections
            """
        ).fetchone()[0]

        return {
            "detections": detections,
            "alerts": alerts,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "high_alerts": high_alerts,
            "cameras": cameras,
            "online_cameras": online_cameras,
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


@router.get("/detections")
def detection_statistics():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                object,
                COUNT(*) AS count,
                AVG(confidence) AS average_confidence
            FROM detections
            GROUP BY object
            ORDER BY count DESC
            """
        ).fetchall()

        objects = []

        for row in rows:
            objects.append(
                {
                    "object": row["object"],
                    "count": row["count"],
                    "average_confidence": (
                        round(
                            row["average_confidence"],
                            3,
                        )
                        if row["average_confidence"] is not None
                        else 0
                    ),
                }
            )

        return {
            "count": len(objects),
            "objects": objects,
        }

    finally:
        connection.close()


@router.get("/alerts")
def alert_statistics():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                priority,
                COUNT(*) AS count
            FROM alerts
            GROUP BY priority
            ORDER BY count DESC
            """
        ).fetchall()

        priorities = [
            {
                "priority": row["priority"],
                "count": row["count"],
            }
            for row in rows
        ]

        return {
            "count": len(priorities),
            "priorities": priorities,
        }

    finally:
        connection.close()


@router.get("/cameras")
def camera_statistics():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                camera,
                COUNT(*) AS detection_count,
                AVG(confidence) AS average_confidence
            FROM detections
            GROUP BY camera
            ORDER BY detection_count DESC
            """
        ).fetchall()

        cameras = []

        for row in rows:
            cameras.append(
                {
                    "camera": row["camera"],
                    "detection_count": row["detection_count"],
                    "average_confidence": (
                        round(
                            row["average_confidence"],
                            3,
                        )
                        if row["average_confidence"] is not None
                        else 0
                    ),
                }
            )

        return {
            "count": len(cameras),
            "cameras": cameras,
        }

    finally:
        connection.close()


@router.get("/timeline")
def statistics_timeline(
    limit: int = 100,
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
            SELECT
                timestamp,
                object,
                camera,
                confidence
            FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        timeline = [
            {
                "timestamp": row["timestamp"],
                "object": row["object"],
                "camera": row["camera"],
                "confidence": row["confidence"],
            }
            for row in rows
        ]

        timeline.reverse()

        return {
            "count": len(timeline),
            "timeline": timeline,
        }

    finally:
        connection.close()
