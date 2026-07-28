import httpx

from src.core.config import settings


class EventClient:
    """
    Client responsible for sending events
    to the Event Service.
    """

    def __init__(self):
        self.base_url = settings.EVENT_SERVICE_URL

    async def publish_detection(
        self,
        camera_id: int,
        detections: list,
    ):

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/events/detection",
                json={
                    "camera_id": camera_id,
                    "detections": detections,
                },
            )

            response.raise_for_status()

            return response.json()


event_client = EventClient()
