from datetime import datetime

from src.core.config import settings


class HealthService:
    """
    Health Service.
    """

    def get_health(self):
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }
