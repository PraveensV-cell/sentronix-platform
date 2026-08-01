from __future__ import annotations

from typing import Optional

import httpx

from src.core.config import settings
from src.core.logger import logger


class CameraClient:
    """
    Client for Camera Service communication.
    """

    def __init__(self):
        self.base_url = settings.CAMERA_SERVICE_URL

        self.client = httpx.AsyncClient(
            timeout=30.0,
        )

    async def get_frame(
        self,
        camera_name: str,
    ) -> Optional[bytes]:
        """
        Request latest camera frame.
        """

        try:
            response = await self.client.get(
                f"{self.base_url}/stream/{camera_name}/frame",
            )

            response.raise_for_status()

            return response.content

        except httpx.HTTPError as error:
            logger.error(
                f"Camera Service request failed: {error}",
            )

            return None

        except Exception as error:
            logger.error(
                f"Camera frame request failed: {error}",
            )

            return None

    async def close(
        self,
    ):
        """
        Close HTTP client.
        """

        await self.client.aclose()


camera_client = CameraClient()
