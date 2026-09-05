import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"


def get_connection():
    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


def ensure_notifications_table():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                object TEXT NOT NULL,
                priority TEXT NOT NULL,
                confidence REAL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'UNREAD'
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def create_notification(alert):
    ensure_notifications_table()

    priority = alert.get(
        "priority",
        "NORMAL",
    )

    if priority not in {
        "CRITICAL",
        "HIGH",
    }:
        return None

    object_name = alert.get(
        "object",
        "unknown",
    )

    confidence = alert.get(
        "confidence",
        0.0,
    )

    message = (
        f"{priority} security alert: "
        f"{object_name} detected "
        f"with {confidence * 100:.1f}% confidence"
    )

    notification = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "object": object_name,
        "priority": priority,
        "confidence": round(
            confidence,
            3,
        ),
        "message": message,
        "status": "UNREAD",
    }

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO notifications (
                timestamp,
                object,
                priority,
                confidence,
                message,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                notification["timestamp"],
                notification["object"],
                notification["priority"],
                notification["confidence"],
                notification["message"],
                notification["status"],
            ),
        )

        connection.commit()

        notification["id"] = cursor.lastrowid

        return notification

    finally:
        connection.close()


def get_notifications(
    limit=50,
    status=None,
):
    ensure_notifications_table()

    connection = get_connection()

    try:
        if status is None:
            rows = connection.execute(
                """
                SELECT
                    id,
                    timestamp,
                    object,
                    priority,
                    confidence,
                    message,
                    status
                FROM notifications
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT
                    id,
                    timestamp,
                    object,
                    priority,
                    confidence,
                    message,
                    status
                FROM notifications
                WHERE status = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    status,
                    limit,
                ),
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def mark_notification_read(
    notification_id,
):
    ensure_notifications_table()

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE notifications
            SET status = 'READ'
            WHERE id = ?
            """,
            (notification_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_unread_count():
    ensure_notifications_table()

    connection = get_connection()

    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM notifications
            WHERE status = 'UNREAD'
            """
        ).fetchone()[0]

        return count

    finally:
        connection.close()
