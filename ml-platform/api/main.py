from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Newly added master modules
from api.auth_api import router as auth_router
from api.environment_api import router as environment_router
from api.people_api import router as people_router
from api.attendance_api import router as attendance_router
from api.rules_api import router as rules_router
from api.assistant_api import router as assistant_router
from api.vision_search_api import router as vision_search_router

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Sentronix AI Platform API",
    description="Intelligent Surveillance, Face Recognition, Attendance & Safety Operations Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core & Surveillance Routers
app.include_router(auth_router)
app.include_router(environment_router)
app.include_router(camera_router)
app.include_router(camera_stream_router)
app.include_router(people_router)
app.include_router(attendance_router)
app.include_router(rules_router)
app.include_router(assistant_router)
app.include_router(vision_search_router)

# Analytics, Health & Monitoring Routers
app.include_router(alert_router)
app.include_router(detection_router)
app.include_router(event_feed_router)
app.include_router(health_router)
app.include_router(inference_router)
app.include_router(monitoring_router)
app.include_router(notification_router)
app.include_router(statistics_router)
app.include_router(realtime_router)


@app.get("/")
def root():
    return {
        "name": "Sentronix AI Platform API",
        "version": "1.0.0",
        "status": "running",
        "ai": "active",
        "documentation": "/docs",
        "redoc": "/redoc",
    }


@app.get("/status")
def status():
    return {
        "AI": "running",
        "database": "connected",
        "version": "1.0.0",
        "service": "Sentronix AI Operations Platform",
    }
