from fastapi import APIRouter

from src.api.v1.endpoints.system import router as system_router
from src.core.config import settings

api_router = APIRouter(prefix=settings.API_PREFIX)

api_router.include_router(
    system_router,
    tags=["System"],
)
