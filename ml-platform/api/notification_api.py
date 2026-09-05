import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
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
def get_notifications(
    limit: int = 50,
):
    limit = max(
        1,
        min(limit, 200),
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        notifications = []

        for row in rows:
            item = dict(row)

            item["type"] = "ALERT"

            notifications.append(item)

        return {
            "count": len(notifications),
            "notifications": notifications,
        }

    finally:
        connection.close()


@router.get("/latest")
def get_latest_notification():
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return {
                "success": False,
                "notification": None,
            }

        notification = dict(row)

        notification["type"] = "ALERT"

        return {
            "success": True,
            "notification": notification,
        }

    finally:
        connection.close()


@router.get("/active")
def get_active_notifications(
    limit: int = 50,
):
    limit = max(
        1,
        min(limit, 200),
    )

    connection = get_connection()

    try:
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

        notifications = []

        for row in rows:
            item = dict(row)

            item["type"] = "ALERT"

            notifications.append(item)

        return {
            "count": len(notifications),
            "notifications": notifications,
        }

    finally:
        connection.close()


@router.get("/critical")
def get_critical_notifications(
    limit: int = 50,
):
    limit = max(
        1,
        min(limit, 200),
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM alerts
            WHERE UPPER(priority) = 'CRITICAL'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        notifications = []

        for row in rows:
            item = dict(row)

            item["type"] = "ALERT"

            notifications.append(item)

        return {
            "count": len(notifications),
            "notifications": notifications,
        }

    finally:
        connection.close()


@router.get("/summary")
def notification_summary():
    connection = get_connection()

    try:
        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            """
        ).fetchone()[0]

        active = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(status) = 'ACTIVE'
            """
        ).fetchone()[0]

        critical = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(priority) = 'CRITICAL'
            """
        ).fetchone()[0]

        high = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(priority) = 'HIGH'
            """
        ).fetchone()[0]

        resolved = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(status) = 'RESOLVED'
            """
        ).fetchone()[0]

        return {
            "total": total,
            "active": active,
            "critical": critical,
            "high": high,
            "resolved": resolved,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    finally:
        connection.close()


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
):
    connection = get_connection()

    try:
        columns = connection.execute(
            """
            PRAGMA table_info(alerts)
            """
        ).fetchall()

        column_names = {row["name"] for row in columns}

        if "read" in column_names:
            connection.execute(
                """
                UPDATE alerts
                SET read = 1
                WHERE id = ?
                """,
                (notification_id,),
            )

        elif "is_read" in column_names:
            connection.execute(
                """
                UPDATE alerts
                SET is_read = 1
                WHERE id = ?
                """,
                (notification_id,),
            )

        else:
            return {
                "success": False,
                "message": "Read field not available",
                "notification_id": notification_id,
            }

        connection.commit()

        return {
            "success": True,
            "message": "Notification marked as read",
            "notification_id": notification_id,
        }

    finally:
        connection.close()


@router.patch("/{notification_id}/resolve")
def resolve_notification(
    notification_id: int,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE alerts
            SET status = 'RESOLVED'
            WHERE id = ?
            """,
            (notification_id,),
        )

        connection.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Notification not found",
                "notification_id": notification_id,
            }

        return {
            "success": True,
            "message": "Notification resolved",
            "notification_id": notification_id,
        }

    finally:
        connection.close()
