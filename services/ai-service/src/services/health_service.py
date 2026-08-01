from __future__ import annotations

from datetime import datetime
from typing import Any

from src.core.config import settings
from src.detector.model_loader import (
    model_loader,
)
from src.detector.tracker import (
    tracker,
)


class HealthService:
    """
    AI Service Health Monitoring.
    """

    def get_health(
        self,
    ) -> dict[str, Any]:
        """
        Basic health status.
        """

        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_details(
        self,
    ) -> dict[str, Any]:
        """
        Detailed AI service status.
        """

        model_info = model_loader.model_info()

        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_info,
            "active_tracked_objects": tracker.active_objects(),
            "tracking_enabled": settings.ENABLE_TRACKING,
            "device": settings.DEVICE,
        }


health_service = HealthService()
