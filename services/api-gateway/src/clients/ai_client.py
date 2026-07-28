from shared.communication.client import ServiceClient


class AIClient(ServiceClient):
    def __init__(self):
        super().__init__(base_url="http://ai-service:8001")

    async def health(self):
        return await self.get("/health")

    async def detect(self, files):
        return await self.post(
            "/detect",
            files=files,
        )
