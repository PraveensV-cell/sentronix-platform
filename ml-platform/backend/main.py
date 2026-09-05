import sqlite3
from pathlib import Path

from backend.api.ml_status import router as ml_status_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"


app = FastAPI(
    title="Sentronix Security AI API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(ml_status_router)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


@app.get("/")
def home():
    return {
        "system": "Sentronix AI Security",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/detections")
def get_detections():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                timestamp,
                camera_id,
                object,
                confidence,
                bbox
            FROM detections
            ORDER BY id DESC
            LIMIT 100
            """
        )

        rows = cursor.fetchall()

        return {
            "count": len(rows),
            "detections": [dict(row) for row in rows],
        }

    finally:
        connection.close()


@app.get("/alerts")
def get_alerts():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
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
            LIMIT 100
            """
        )

        rows = cursor.fetchall()

        return {
            "count": len(rows),
            "alerts": [dict(row) for row in rows],
        }

    finally:
        connection.close()


@app.get("/cameras")
def get_cameras():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                camera_name,
                location,
                status
            FROM cameras
            ORDER BY id ASC
            """
        )

        rows = cursor.fetchall()

        return {
            "count": len(rows),
            "cameras": [dict(row) for row in rows],
        }

    finally:
        connection.close()


@app.get("/status")
def status():
    connection = get_connection()

    try:
        connection.execute("SELECT 1")

        return {
            "AI": "running",
            "database": "connected",
            "version": "1.0.0",
        }

    finally:
        connection.close()
