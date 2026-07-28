from fastapi import APIRouter

from src.api.routes.device import router as device_router
from src.api.routes.health import router as health_router

api_router = APIRouter()

api_router.include_router(
    device_router,
    prefix="/device",
    tags=["Device"],
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)
