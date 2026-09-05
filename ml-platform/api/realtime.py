import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/realtime",
    tags=["Realtime"],
)

active_connections = set()


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


def get_system_status():
    connection = get_connection()

    try:
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

        return {
            "status": "RUNNING",
            "cameras": cameras,
            "online_cameras": online_cameras,
            "detections": detections,
            "alerts": alerts,
            "active_alerts": active_alerts,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    finally:
        connection.close()


@router.get("")
def realtime_status():
    return {
        "service": "Sentronix Realtime Engine",
        "status": "running",
        "connections": len(active_connections),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/status")
def realtime_system_status():
    return get_system_status()


@router.get("/events")
def realtime_events():
    connection = get_connection()

    try:
        detections = connection.execute(
            """
            SELECT *
            FROM detections
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

        alerts = connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

        events = []

        for row in detections:
            item = dict(row)
            item["type"] = "DETECTION"
            events.append(item)

        for row in alerts:
            item = dict(row)
            item["type"] = "ALERT"
            events.append(item)

        events.sort(
            key=lambda item: item.get(
                "timestamp",
                "",
            ),
            reverse=True,
        )

        return {
            "count": len(events),
            "events": events[:20],
        }

    finally:
        connection.close()


@router.websocket("/ws")
async def realtime_websocket(
    websocket: WebSocket,
):
    await websocket.accept()

    active_connections.add(websocket)

    last_detection_id = None
    last_alert_id = None

    try:
        await websocket.send_json(
            {
                "type": "CONNECTED",
                "service": "Sentronix Realtime Engine",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        while True:
            connection = get_connection()

            try:
                detection = connection.execute(
                    """
                    SELECT *
                    FROM detections
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ).fetchone()

                alert = connection.execute(
                    """
                    SELECT *
                    FROM alerts
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ).fetchone()

            finally:
                connection.close()

            if detection is not None and detection["id"] != last_detection_id:
                last_detection_id = detection["id"]

                message = dict(detection)

                message["type"] = "DETECTION"

                await websocket.send_json(message)

            if alert is not None and alert["id"] != last_alert_id:
                last_alert_id = alert["id"]

                message = dict(alert)

                message["type"] = "ALERT"

                await websocket.send_json(message)

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        active_connections.discard(websocket)

    except Exception:
        active_connections.discard(websocket)


@router.websocket("/ws/status")
async def realtime_status_websocket(
    websocket: WebSocket,
):
    await websocket.accept()

    active_connections.add(websocket)

    try:
        while True:
            status = get_system_status()

            await websocket.send_json(
                {
                    "type": "SYSTEM_STATUS",
                    "data": status,
                }
            )

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        active_connections.discard(websocket)

    except Exception:
        active_connections.discard(websocket)
