from datetime import datetime

from src.core.config import settings
from src.schemas.health import HealthResponse

APP_START_TIME = datetime.utcnow()


def get_uptime() -> str:
    delta = datetime.utcnow() - APP_START_TIME

    total_seconds = int(delta.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def health_status() -> HealthResponse:
    return HealthResponse(
        service=settings.APP_NAME,
        status="healthy",
        version=settings.APP_VERSION,
        uptime=get_uptime(),
        timestamp=datetime.utcnow(),
    )
