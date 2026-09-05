from pathlib import Path

from api.alert_api import router as alert_router
from api.camera_api import router as camera_router
from api.camera_stream import router as camera_stream_router
from api.detection_api import router as detection_router
from api.event_feed_api import router as event_feed_router
from api.health_api import router as health_router
from api.inference_api import router as inference_router
from api.monitoring_api import router as monitoring_router
from api.notification_api import router as notification_router
from api.realtime import router as realtime_router
from api.statistics_api import router as statistics_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI(
    title="Sentronix Platform API",
    description="AI-powered real-time monitoring and detection platform",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(alert_router)
app.include_router(camera_router)
app.include_router(detection_router)
app.include_router(event_feed_router)
app.include_router(health_router)
app.include_router(inference_router)
app.include_router(monitoring_router)
app.include_router(notification_router)
app.include_router(statistics_router)
app.include_router(camera_stream_router)
app.include_router(realtime_router)


@app.get("/")
def root():
    return {
        "name": "Sentronix Platform API",
        "version": "1.0.0",
        "status": "running",
        "ai": "running",
        "documentation": "/docs",
        "redoc": "/redoc",
    }


@app.get("/status")
def status():
    return {
        "AI": "running",
        "database": "connected",
        "version": "1.0.0",
        "service": "Sentronix Platform API",
    }
