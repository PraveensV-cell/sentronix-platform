import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=5,
    )

    connection.row_factory = sqlite3.Row

    return connection


def check_database():
    start = time.perf_counter()

    try:
        connection = get_connection()

        connection.execute("SELECT 1").fetchone()

        connection.close()

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "healthy",
            "response_time_ms": round(
                elapsed,
                2,
            ),
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "error": str(error),
        }


def check_database_tables():
    required_tables = {
        "detections",
        "alerts",
        "cameras",
    }

    try:
        connection = get_connection()

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        connection.close()

        existing_tables = {row["name"] for row in rows}

        missing_tables = sorted(required_tables - existing_tables)

        if missing_tables:
            return {
                "status": "degraded",
                "required_tables": sorted(required_tables),
                "missing_tables": missing_tables,
            }

        return {
            "status": "healthy",
            "required_tables": sorted(required_tables),
            "missing_tables": [],
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "required_tables": sorted(required_tables),
            "missing_tables": [],
            "error": str(error),
        }


@router.get("")
def health_check():
    database = check_database()
    tables = check_database_tables()

    if database["status"] == "healthy" and tables["status"] == "healthy":
        overall_status = "healthy"

    elif database["status"] == "unhealthy":
        overall_status = "unhealthy"

    else:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "Sentronix API",
        "version": "1.0.0",
        "database": database,
        "tables": tables,
    }


@router.get("/database")
def database_health():
    return check_database()


@router.get("/tables")
def table_health():
    return check_database_tables()


@router.get("/live")
def liveness():
    return {
        "status": "alive",
        "service": "Sentronix API",
    }


@router.get("/ready")
def readiness():
    database = check_database()

    if database["status"] != "healthy":
        return {
            "status": "not_ready",
            "database": database,
        }

    return {
        "status": "ready",
        "database": database,
    }
