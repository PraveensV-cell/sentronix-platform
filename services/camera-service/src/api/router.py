from fastapi import APIRouter

from src.api.routes.camera import (
    router as camera_router,
)
from src.api.routes.stream import (
    router as stream_router,
)
from src.api.routes.health import (
    router as health_router,
)

api_router = APIRouter()

api_router.include_router(
    camera_router,
)

api_router.include_router(
    stream_router,
)

api_router.include_router(
    health_router,
)
