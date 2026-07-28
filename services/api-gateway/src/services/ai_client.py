import httpx

from src.core.config import settings


class AIClient:
    """
    Client for communicating with the AI Service.
    """

    def __init__(self):
        self.base_url = settings.AI_SERVICE_URL

    async def health(self):

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/health")

            response.raise_for_status()

            return response.json()

    async def detect(
        self,
        image_path: str,
    ):

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/detect",
                json={
                    "image_path": image_path,
                },
            )

            response.raise_for_status()

            return response.json()


ai_client = AIClient()
