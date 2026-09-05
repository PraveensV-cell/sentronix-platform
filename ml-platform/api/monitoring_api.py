import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


def table_exists(
    connection,
    table_name,
):
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


@router.get("")
def get_monitoring_status():
    connection = get_connection()

    try:
        database_status = "CONNECTED"

        detection_count = 0
        alert_count = 0
        active_alert_count = 0
        camera_count = 0
        online_camera_count = 0

        if table_exists(
            connection,
            "detections",
        ):
            detection_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM detections
                """
            ).fetchone()[0]

        if table_exists(
            connection,
            "alerts",
        ):
            alert_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM alerts
                """
            ).fetchone()[0]

            active_alert_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM alerts
                WHERE UPPER(status) = 'ACTIVE'
                """
            ).fetchone()[0]

        if table_exists(
            connection,
            "cameras",
        ):
            camera_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM cameras
                """
            ).fetchone()[0]

            online_camera_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM cameras
                WHERE UPPER(status) = 'ONLINE'
                """
            ).fetchone()[0]

        return {
            "status": "RUNNING",
            "database": database_status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cameras": {
                "total": camera_count,
                "online": online_camera_count,
                "offline": (camera_count - online_camera_count),
            },
            "detections": {
                "total": detection_count,
            },
            "alerts": {
                "total": alert_count,
                "active": active_alert_count,
            },
        }

    finally:
        connection.close()


@router.get("/cameras")
def monitor_cameras():
    connection = get_connection()

    try:
        if not table_exists(
            connection,
            "cameras",
        ):
            return {
                "count": 0,
                "cameras": [],
            }

        rows = connection.execute(
            """
            SELECT *
            FROM cameras
            ORDER BY id ASC
            """
        ).fetchall()

        cameras = []

        for row in rows:
            camera = dict(row)

            status = str(
                camera.get(
                    "status",
                    "OFFLINE",
                )
            ).upper()

            camera["online"] = status == "ONLINE"

            cameras.append(camera)

        return {
            "count": len(cameras),
            "cameras": cameras,
        }

    finally:
        connection.close()


@router.get("/alerts")
def monitor_alerts(
    limit: int = 20,
):
    limit = max(
        1,
        min(
            limit,
            200,
        ),
    )

    connection = get_connection()

    try:
        if not table_exists(
            connection,
            "alerts",
        ):
            return {
                "count": 0,
                "alerts": [],
            }

        rows = connection.execute(
            """
            SELECT *
            FROM alerts
            WHERE UPPER(status) = 'ACTIVE'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        alerts = [dict(row) for row in rows]

        return {
            "count": len(alerts),
            "alerts": alerts,
        }

    finally:
        connection.close()


@router.get("/activity")
def monitor_activity(
    limit: int = 30,
):
    limit = max(
        1,
        min(
            limit,
            200,
        ),
    )

    connection = get_connection()

    try:
        activity = []

        if table_exists(
            connection,
            "detections",
        ):
            detection_rows = connection.execute(
                """
                SELECT
                    id,
                    timestamp,
                    camera,
                    object,
                    confidence
                FROM detections
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            for row in detection_rows:
                item = dict(row)

                item["type"] = "DETECTION"

                activity.append(item)

        if table_exists(
            connection,
            "alerts",
        ):
            alert_rows = connection.execute(
                """
                SELECT
                    id,
                    timestamp,
                    object,
                    priority,
                    confidence,
                    status
                FROM alerts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            for row in alert_rows:
                item = dict(row)

                item["type"] = "ALERT"

                activity.append(item)

        activity.sort(
            key=lambda item: item.get(
                "timestamp",
                "",
            ),
            reverse=True,
        )

        activity = activity[:limit]

        return {
            "count": len(activity),
            "activity": activity,
        }

    finally:
        connection.close()


@router.get("/summary")
def monitoring_summary():
    connection = get_connection()

    try:
        detections = 0
        alerts = 0
        active_alerts = 0
        cameras = 0
        online_cameras = 0

        if table_exists(
            connection,
            "detections",
        ):
            detections = connection.execute(
                """
                SELECT COUNT(*)
                FROM detections
                """
            ).fetchone()[0]

        if table_exists(
            connection,
            "alerts",
        ):
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

        if table_exists(
            connection,
            "cameras",
        ):
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

        return {
            "system": "Sentronix",
            "status": "OPERATIONAL",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": {
                "cameras": cameras,
                "online_cameras": online_cameras,
                "detections": detections,
                "alerts": alerts,
                "active_alerts": active_alerts,
            },
        }

    finally:
        connection.close()
