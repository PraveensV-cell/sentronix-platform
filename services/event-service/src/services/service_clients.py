from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings
from src.core.logger import logger


class ServiceClients:
    """
    Handles communication with downstream services.
    """

    def __init__(self):

        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
        )

        self.notification_url = settings.NOTIFICATION_SERVICE_URL

        self.storage_url = settings.STORAGE_SERVICE_URL

        self.analytics_url = settings.ANALYTICS_SERVICE_URL

    async def notify(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Send event to notification service.
        """

        await self._send(
            f"{self.notification_url}/events",
            event,
            "Notification",
        )

    async def store(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Send event to storage service.
        """

        await self._send(
            f"{self.storage_url}/events",
            event,
            "Storage",
        )

    async def analyze(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Send event to analytics service.
        """

        await self._send(
            f"{self.analytics_url}/events",
            event,
            "Analytics",
        )

    async def _send(
        self,
        url: str,
        payload: dict[str, Any],
        service_name: str,
    ) -> None:
        """
        Common HTTP sender.
        """

        try:
            response = await self.client.post(
                url,
                json=payload,
            )

            response.raise_for_status()

        except Exception as error:
            logger.error(
                f"{service_name} service communication failed: {error}",
            )

    async def close(
        self,
    ) -> None:
        """
        Close HTTP client.
        """

        await self.client.aclose()


service_clients = ServiceClients()
