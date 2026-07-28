import httpx

from src.core.config import settings


class ServiceClients:
    """
    Handles communication with downstream services.
    """

    def __init__(self):

        self.notification_url = settings.NOTIFICATION_SERVICE_URL

        self.storage_url = settings.STORAGE_SERVICE_URL

        self.analytics_url = settings.ANALYTICS_SERVICE_URL

    async def notify(
        self,
        event: dict,
    ):

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.notification_url}/events",
                    json=event,
                )

                response.raise_for_status()

            except Exception:
                pass

    async def store(
        self,
        event: dict,
    ):

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.storage_url}/events",
                    json=event,
                )

                response.raise_for_status()

            except Exception:
                pass

    async def analyze(
        self,
        event: dict,
    ):

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.analytics_url}/events",
                    json=event,
                )

                response.raise_for_status()

            except Exception:
                pass


service_clients = ServiceClients()
