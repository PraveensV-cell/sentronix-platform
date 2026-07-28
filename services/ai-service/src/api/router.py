from fastapi import APIRouter

from src.api.routes.health import router as health_router
from src.api.routes.detection import router as detection_router
from src.api.routes.video_detection import router as video_detection_router
from src.api.routes.live_detection import router as live_detection_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(detection_router)
api_router.include_router(video_detection_router)
api_router.include_router(live_detection_router)
