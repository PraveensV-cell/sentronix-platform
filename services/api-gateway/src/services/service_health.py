import httpx

from src.core.config import settings


class ServiceHealth:
    async def check(
        self,
        name: str,
        url: str,
    ):

        try:
            async with httpx.AsyncClient(
                timeout=5.0,
            ) as client:
                response = await client.get(
                    f"{url}/health",
                )

                return {
                    "service": name,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                }

        except Exception as exc:
            return {
                "service": name,
                "status": "offline",
                "error": str(exc),
            }

    async def check_all(self):

        return {
            "gateway": "healthy",
            "services": [
                await self.check(
                    "ai-service",
                    settings.AI_SERVICE_URL,
                ),
                await self.check(
                    "event-service",
                    settings.EVENT_SERVICE_URL,
                ),
                await self.check(
                    "notification-service",
                    settings.NOTIFICATION_SERVICE_URL,
                ),
                await self.check(
                    "storage-service",
                    settings.STORAGE_SERVICE_URL,
                ),
                await self.check(
                    "analytics-service",
                    settings.ANALYTICS_SERVICE_URL,
                ),
            ],
        }


service_health = ServiceHealth()
