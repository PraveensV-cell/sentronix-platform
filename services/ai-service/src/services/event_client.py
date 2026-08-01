from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings
from src.core.logger import logger


class EventClient:
    """
    Client for communicating with Event Service.
    """

    def __init__(self):
        self.base_url = settings.EVENT_SERVICE_URL

        self.client = httpx.AsyncClient(
            timeout=30.0,
        )

    async def publish_detection(
        self,
        camera_id: int,
        detections: list[dict[str, Any]],
    ):
        """
        Send detection event to Event Service.
        """

        payload = {
            "camera_id": camera_id,
            "detections": detections,
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/events/detection",
                json=payload,
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as error:
            logger.error(
                f"Event Service request failed: {error}",
            )

            raise

        except Exception as error:
            logger.error(
                f"Event publish failed: {error}",
            )

            raise

    async def close(
        self,
    ):
        """
        Close HTTP client.
        """

        await self.client.aclose()


event_client = EventClient()
