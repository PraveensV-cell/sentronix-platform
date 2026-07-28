from datetime import datetime

from fastapi import APIRouter

from src.core.config import settings
from src.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
)
async def health():

    return HealthResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.get("/ping")
async def ping():

    return {"message": "pong"}
