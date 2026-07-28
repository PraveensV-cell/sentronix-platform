from fastapi import APIRouter

from src.api.routes.analytics import router as analytics_router
from src.api.routes.health import router as health_router

api_router = APIRouter()

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"],
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)
