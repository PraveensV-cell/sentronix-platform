from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from src.core.config import settings
from src.schemas.health import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "/",
    response_model=HealthResponse,
)
async def health():
    """
    Health check endpoint.
    """

    return HealthResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/ping",
)
async def ping():
    """
    Simple connectivity check.
    """

    return {
        "message": "pong",
    }
