from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings
from src.core.logger import logger


class ServiceClient:
    """
    Client for communicating with other services.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
        )

    async def send_notification(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Send event notification.
        """

        try:
            response = await self.client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/notification/",
                json={
                    "recipient": "admin@sentronix.com",
                    "subject": "AI Detection Event",
                    "message": (
                        f"Camera {event['camera_id']} detected "
                        f"{len(event['detections'])} object(s)."
                    ),
                    "channel": "email",
                },
            )

            response.raise_for_status()

        except Exception as error:
            logger.error(
                f"Notification Service Error: {error}",
            )

    async def store_event(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Store event in storage service.
        """

        try:
            response = await self.client.post(
                f"{settings.STORAGE_SERVICE_URL}/storage/events",
                json=event,
            )

            response.raise_for_status()

        except Exception as error:
            logger.error(
                f"Storage Service Error: {error}",
            )

    async def update_analytics(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Send event to analytics service.
        """

        try:
            response = await self.client.post(
                f"{settings.ANALYTICS_SERVICE_URL}/analytics/events",
                json=event,
            )

            response.raise_for_status()

        except Exception as error:
            logger.error(
                f"Analytics Service Error: {error}",
            )

    async def close(
        self,
    ) -> None:
        """
        Close HTTP client.
        """

        await self.client.aclose()


service_client = ServiceClient()
