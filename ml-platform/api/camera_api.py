import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


def get_columns(
    connection,
):
    rows = connection.execute("PRAGMA table_info(cameras)").fetchall()

    return [row["name"] for row in rows]


def ensure_table(
    connection,
):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT UNIQUE,
            name TEXT,
            source TEXT,
            camera_type TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    connection.commit()


def row_to_dict(
    row,
):
    if row is None:
        return None

    return dict(row)


@router.get("")
def get_cameras():
    connection = get_connection()

    try:
        ensure_table(connection)

        rows = connection.execute(
            """
            SELECT *
            FROM cameras
            ORDER BY id ASC
            """
        ).fetchall()

        cameras = [row_to_dict(row) for row in rows]

        return {
            "count": len(cameras),
            "cameras": cameras,
        }

    finally:
        connection.close()


@router.get("/{camera_id}")
def get_camera(
    camera_id: str,
):
    connection = get_connection()

    try:
        ensure_table(connection)

        columns = get_columns(connection)

        if "camera_id" in columns:
            row = connection.execute(
                """
                SELECT *
                FROM cameras
                WHERE camera_id = ?
                """,
                (camera_id,),
            ).fetchone()
        else:
            try:
                row = connection.execute(
                    """
                    SELECT *
                    FROM cameras
                    WHERE id = ?
                    """,
                    (int(camera_id),),
                ).fetchone()
            except ValueError:
                row = None

        if row is None:
            return {
                "success": False,
                "message": "Camera not found",
            }

        return {
            "success": True,
            "camera": row_to_dict(row),
        }

    finally:
        connection.close()


@router.post("")
def create_camera(
    camera_id: str,
    name: str,
    source: str,
    camera_type: str = "USB",
):
    connection = get_connection()

    try:
        ensure_table(connection)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        existing = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        if existing is not None:
            return {
                "success": False,
                "message": "Camera already exists",
                "camera": row_to_dict(existing),
            }

        connection.execute(
            """
            INSERT INTO cameras (
                camera_id,
                name,
                source,
                camera_type,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                camera_id,
                name,
                source,
                camera_type,
                "OFFLINE",
                now,
                now,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        return {
            "success": True,
            "message": "Camera created",
            "camera": row_to_dict(row),
        }

    finally:
        connection.close()


@router.put("/{camera_id}")
def update_camera(
    camera_id: str,
    name: str,
    source: str,
    camera_type: str = "USB",
):
    connection = get_connection()

    try:
        ensure_table(connection)

        existing = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        if existing is None:
            return {
                "success": False,
                "message": "Camera not found",
            }

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE cameras
            SET
                name = ?,
                source = ?,
                camera_type = ?,
                updated_at = ?
            WHERE camera_id = ?
            """,
            (
                name,
                source,
                camera_type,
                now,
                camera_id,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        return {
            "success": True,
            "message": "Camera updated",
            "camera": row_to_dict(row),
        }

    finally:
        connection.close()


@router.patch("/{camera_id}/status")
def update_camera_status(
    camera_id: str,
    status: str,
):
    allowed_statuses = {
        "ONLINE",
        "OFFLINE",
        "CONNECTING",
        "ERROR",
        "DISABLED",
    }

    status = status.upper()

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid camera status",
            "allowed": sorted(allowed_statuses),
        }

    connection = get_connection()

    try:
        ensure_table(connection)

        existing = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        if existing is None:
            return {
                "success": False,
                "message": "Camera not found",
            }

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE cameras
            SET
                status = ?,
                updated_at = ?
            WHERE camera_id = ?
            """,
            (
                status,
                now,
                camera_id,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        return {
            "success": True,
            "camera": row_to_dict(row),
        }

    finally:
        connection.close()


@router.delete("/{camera_id}")
def delete_camera(
    camera_id: str,
):
    connection = get_connection()

    try:
        ensure_table(connection)

        existing = connection.execute(
            """
            SELECT *
            FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        ).fetchone()

        if existing is None:
            return {
                "success": False,
                "message": "Camera not found",
            }

        connection.execute(
            """
            DELETE FROM cameras
            WHERE camera_id = ?
            """,
            (camera_id,),
        )

        connection.commit()

        return {
            "success": True,
            "message": "Camera deleted",
            "camera_id": camera_id,
        }

    finally:
        connection.close()


@router.get("/statistics/summary")
def camera_statistics():
    connection = get_connection()

    try:
        ensure_table(connection)

        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            """
        ).fetchone()[0]

        online = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            WHERE UPPER(status) = 'ONLINE'
            """
        ).fetchone()[0]

        offline = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            WHERE UPPER(status) = 'OFFLINE'
            """
        ).fetchone()[0]

        connecting = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            WHERE UPPER(status) = 'CONNECTING'
            """
        ).fetchone()[0]

        errors = connection.execute(
            """
            SELECT COUNT(*)
            FROM cameras
            WHERE UPPER(status) = 'ERROR'
            """
        ).fetchone()[0]

        return {
            "total": total,
            "online": online,
            "offline": offline,
            "connecting": connecting,
            "errors": errors,
        }

    finally:
        connection.close()
