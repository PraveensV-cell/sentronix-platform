from fastapi import APIRouter

from src.api.routes.event import router as event_router
from src.api.routes.health import router as health_router

api_router = APIRouter()

api_router.include_router(
    event_router,
    prefix="/events",
    tags=["Events"],
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)
