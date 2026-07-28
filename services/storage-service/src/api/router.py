from fastapi import APIRouter

from src.api.routes.health import router as health_router
from src.api.routes.storage import router as storage_router

api_router = APIRouter()

api_router.include_router(
    storage_router,
    prefix="/storage",
    tags=["Storage"],
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)
