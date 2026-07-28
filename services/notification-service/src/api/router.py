from fastapi import APIRouter

from src.api.routes.health import router as health_router
from src.api.routes.notification import router as notification_router

api_router = APIRouter()

api_router.include_router(
    notification_router,
    prefix="/notifications",
    tags=["Notifications"],
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)
