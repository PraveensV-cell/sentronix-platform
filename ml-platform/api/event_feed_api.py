import json
import sqlite3
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/events",
    tags=["Event Feed"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


def decode_bbox(value):
    if value is None:
        return None

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    return value


def normalize_detection(row):
    event = dict(row)

    if "bbox" in event:
        event["bbox"] = decode_bbox(event["bbox"])

    return event


@router.get("")
def get_event_feed(
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
        detections = connection.execute(
            """
            SELECT
                id,
                timestamp,
                camera,
                object,
                confidence,
                bbox
            FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        events = []

        for row in detections:
            event = normalize_detection(row)

            event["event_type"] = "DETECTION"

            events.append(event)

        alerts = connection.execute(
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

        for row in alerts:
            alert = dict(row)

            alert["event_type"] = "ALERT"

            events.append(alert)

        events.sort(
            key=lambda item: item.get(
                "timestamp",
                "",
            ),
            reverse=True,
        )

        events = events[:limit]

        return {
            "count": len(events),
            "events": events,
        }

    finally:
        connection.close()


@router.get("/detections")
def get_detection_feed(
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
            SELECT
                id,
                timestamp,
                camera,
                object,
                confidence,
                bbox
            FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        events = []

        for row in rows:
            event = normalize_detection(row)

            event["event_type"] = "DETECTION"

            events.append(event)

        return {
            "count": len(events),
            "events": events,
        }

    finally:
        connection.close()


@router.get("/alerts")
def get_alert_feed(
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

        events = []

        for row in rows:
            event = dict(row)

            event["event_type"] = "ALERT"

            events.append(event)

        return {
            "count": len(events),
            "events": events,
        }

    finally:
        connection.close()


@router.get("/camera/{camera_id}")
def get_camera_event_feed(
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
        detections = connection.execute(
            """
            SELECT
                id,
                timestamp,
                camera,
                object,
                confidence,
                bbox
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

        events = []

        for row in detections:
            event = normalize_detection(row)

            event["event_type"] = "DETECTION"

            events.append(event)

        return {
            "camera": camera_id,
            "count": len(events),
            "events": events,
        }

    finally:
        connection.close()


@router.get("/latest")
def get_latest_event():
    connection = get_connection()

    try:
        detection = connection.execute(
            """
            SELECT
                id,
                timestamp,
                camera,
                object,
                confidence,
                bbox
            FROM detections
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        alert = connection.execute(
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
            LIMIT 1
            """
        ).fetchone()

        latest_detection = normalize_detection(detection) if detection else None

        latest_alert = dict(alert) if alert else None

        if latest_detection:
            latest_detection["event_type"] = "DETECTION"

        if latest_alert:
            latest_alert["event_type"] = "ALERT"

        candidates = [
            item
            for item in [
                latest_detection,
                latest_alert,
            ]
            if item is not None
        ]

        if not candidates:
            return {
                "success": False,
                "message": "No events found",
            }

        latest = max(
            candidates,
            key=lambda item: item.get(
                "timestamp",
                "",
            ),
        )

        return {
            "success": True,
            "event": latest,
        }

    finally:
        connection.close()


@router.get("/statistics")
def get_event_statistics():
    connection = get_connection()

    try:
        detection_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM detections
            """
        ).fetchone()[0]

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

        total_events = detection_count + alert_count

        return {
            "total_events": total_events,
            "detections": detection_count,
            "alerts": alert_count,
            "active_alerts": active_alert_count,
        }

    finally:
        connection.close()
