import httpx

from src.core.config import settings
from src.core.logger import logger


class ServiceClient:
    async def send_notification(
        self,
        event: dict,
    ):

        try:
            async with httpx.AsyncClient(
                timeout=settings.REQUEST_TIMEOUT,
            ) as client:
                await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/notification/",
                    json={
                        "recipient": "admin@sentronix.com",
                        "subject": "AI Detection Event",
                        "message": f"Camera {event['camera_id']} detected {len(event['detections'])} object(s).",
                        "channel": "email",
                    },
                )

        except Exception as exc:
            logger.error(f"Notification Service Error : {exc}")

    async def store_event(
        self,
        event: dict,
    ):

        try:
            async with httpx.AsyncClient(
                timeout=settings.REQUEST_TIMEOUT,
            ) as client:
                await client.post(
                    f"{settings.STORAGE_SERVICE_URL}/storage/events",
                    json=event,
                )

        except Exception as exc:
            logger.error(f"Storage Service Error : {exc}")

    async def update_analytics(
        self,
        event: dict,
    ):

        try:
            async with httpx.AsyncClient(
                timeout=settings.REQUEST_TIMEOUT,
            ) as client:
                await client.post(
                    f"{settings.ANALYTICS_SERVICE_URL}/analytics/events",
                    json=event,
                )

        except Exception as exc:
            logger.error(f"Analytics Service Error : {exc}")


service_client = ServiceClient()
