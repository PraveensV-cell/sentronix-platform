import httpx

from src.core.config import settings


class ServiceClients:
    """
    Handles communication with other Sentronix services.
    """

    async def ai_health(self):

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.AI_SERVICE_URL}/health")

            return response.json()

    async def events(self):

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.EVENT_SERVICE_URL}/detection")

            return response.json()

    async def notifications(self):

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.NOTIFICATION_SERVICE_URL}/")

            return response.json()

    async def storage(self):

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.STORAGE_SERVICE_URL}/files")

            return response.json()


service_clients = ServiceClients()
