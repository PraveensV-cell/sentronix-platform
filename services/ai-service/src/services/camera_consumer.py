from __future__ import annotations

from typing import Optional, Callable, Awaitable

from src.core.logger import logger
from src.services.camera_client import (
    camera_client,
)


class CameraConsumer:
    """
    Consumes frames from Camera Service.
    """

    async def consume(
        self,
        camera_name: str,
    ) -> Optional[bytes]:
        """
        Get a single camera frame.
        """

        try:
            return await camera_client.get_frame(
                camera_name,
            )

        except Exception as error:
            logger.error(
                f"Camera consume failed: {error}",
            )

            return None

    async def stream(
        self,
        camera_name: str,
        callback: Callable[
            [bytes],
            Awaitable[None],
        ],
        interval: float = 0.1,
    ):
        """
        Continuously consume camera frames.
        """

        import asyncio

        while True:
            frame = await self.consume(
                camera_name,
            )

            if frame is not None:
                try:
                    await callback(
                        frame,
                    )

                except Exception as error:
                    logger.error(
                        f"Frame callback failed: {error}",
                    )

            await asyncio.sleep(
                interval,
            )


camera_consumer = CameraConsumer()
