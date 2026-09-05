import sqlite3
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
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
def get_alerts(
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
            FROM alerts
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


@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM alerts
            WHERE id = ?
            """,
            (alert_id,),
        ).fetchone()

        if row is None:
            return {
                "success": False,
                "message": "Alert not found",
            }

        return {
            "success": True,
            "alert": dict(row),
        }

    finally:
        connection.close()


@router.get("/priority/{priority}")
def get_alerts_by_priority(
    priority: str,
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
            FROM alerts
            WHERE UPPER(priority) = UPPER(?)
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                priority,
                limit,
            ),
        ).fetchall()

        alerts = [dict(row) for row in rows]

        return {
            "priority": priority.upper(),
            "count": len(alerts),
            "alerts": alerts,
        }

    finally:
        connection.close()


@router.get("/object/{object_name}")
def get_alerts_by_object(
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
            FROM alerts
            WHERE LOWER(object) = LOWER(?)
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                object_name,
                limit,
            ),
        ).fetchall()

        alerts = [dict(row) for row in rows]

        return {
            "object": object_name,
            "count": len(alerts),
            "alerts": alerts,
        }

    finally:
        connection.close()


@router.get("/active/list")
def get_active_alerts(
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


@router.get("/statistics/summary")
def get_alert_statistics():
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

        normal = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(priority) = 'NORMAL'
            """
        ).fetchone()[0]

        low = connection.execute(
            """
            SELECT COUNT(*)
            FROM alerts
            WHERE UPPER(priority) = 'LOW'
            """
        ).fetchone()[0]

        return {
            "total": total,
            "active": active,
            "critical": critical,
            "high": high,
            "normal": normal,
            "low": low,
        }

    finally:
        connection.close()


@router.patch("/{alert_id}/status")
def update_alert_status(
    alert_id: int,
    status: str,
):
    allowed_statuses = {
        "ACTIVE",
        "RESOLVED",
        "DISMISSED",
    }

    status = status.upper()

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid status",
            "allowed": sorted(allowed_statuses),
        }

    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT *
            FROM alerts
            WHERE id = ?
            """,
            (alert_id,),
        ).fetchone()

        if existing is None:
            return {
                "success": False,
                "message": "Alert not found",
            }

        connection.execute(
            """
            UPDATE alerts
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                alert_id,
            ),
        )

        connection.commit()

        updated = connection.execute(
            """
            SELECT *
            FROM alerts
            WHERE id = ?
            """,
            (alert_id,),
        ).fetchone()

        return {
            "success": True,
            "alert": dict(updated),
        }

    finally:
        connection.close()
