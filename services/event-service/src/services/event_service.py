import asyncio
import uuid
from datetime import datetime
from typing import Any

from src.core.logger import logger
from src.schemas.event import EventCreate
from src.schemas.event import EventResponse
from src.services.service_client import service_client


class EventService:
    def __init__(self):

        self.events: list[EventResponse] = []

        self.detection_events: list[dict[str, Any]] = []

    def create_event(
        self,
        request: EventCreate,
    ) -> EventResponse:

        event = EventResponse(
            event_id=str(uuid.uuid4()),
            event_type=request.event_type,
            source=request.source,
            description=request.description,
            created_at=datetime.utcnow(),
        )

        self.events.append(event)

        logger.info(f"New Event Created : {event.event_type}")

        return event

    def get_events(
        self,
    ) -> list[EventResponse]:

        return self.events

    def get_event(
        self,
        event_id: str,
    ):

        for event in self.events:
            if event.event_id == event_id:
                return event

        return None

    def delete_event(
        self,
        event_id: str,
    ) -> bool:

        for event in self.events:
            if event.event_id == event_id:
                self.events.remove(event)

                logger.info(f"Deleted Event : {event.event_id}")

                return True

        return False

    # ==========================================================
    # AI Detection Events
    # ==========================================================

    def create_detection_event(
        self,
        camera_id: int,
        detections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create and store an AI detection event.
        """

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "AI_DETECTION",
            "camera_id": camera_id,
            "detections": detections,
            "created_at": datetime.utcnow().isoformat(),
        }

        self.detection_events.append(event)

        logger.info(
            f"Detection Event Created | Camera={camera_id} | Objects={len(detections)}"
        )

        # ==========================================================
        # Forward Event To Other Services
        # ==========================================================

        try:
            asyncio.create_task(service_client.send_notification(event))

            asyncio.create_task(service_client.store_event(event))

            asyncio.create_task(service_client.update_analytics(event))

            logger.info("Detection Event forwarded to all services.")

        except Exception as exc:
            logger.error(f"Event Forwarding Failed : {exc}")

        return event

    def get_detection_events(
        self,
    ) -> list[dict[str, Any]]:

        return self.detection_events

    def get_detection_event(
        self,
        event_id: str,
    ):

        for event in self.detection_events:
            if event["event_id"] == event_id:
                return event

        return None


event_service = EventService()
