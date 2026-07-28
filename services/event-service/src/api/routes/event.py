from asyncio import create_task

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from src.schemas.event import EventCreate
from src.schemas.event import EventResponse
from src.services.event_service import event_service
from src.services.service_clients import service_clients

router = APIRouter()


class DetectionEventRequest(BaseModel):
    camera_id: int
    detections: list[dict]


@router.post(
    "/",
    response_model=EventResponse,
)
async def create_event(
    event: EventCreate,
):
    """
    Create a new event.
    """

    return event_service.create_event(event)


@router.get(
    "/",
    response_model=list[EventResponse],
)
async def get_events():
    """
    Get all events.
    """

    return event_service.get_events()


@router.get(
    "/{event_id}",
    response_model=EventResponse,
)
async def get_event(
    event_id: str,
):
    """
    Get a single event.
    """

    event = event_service.get_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return event


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
):
    """
    Delete an event.
    """

    success = event_service.delete_event(event_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return {
        "message": "Event deleted successfully",
    }


# ==========================================================
# AI Detection Events
# ==========================================================


@router.post("/detection")
async def create_detection_event(
    request: DetectionEventRequest,
):
    """
    Receive AI detection events.
    """

    event = event_service.create_detection_event(
        camera_id=request.camera_id,
        detections=request.detections,
    )

    # Forward asynchronously
    create_task(service_clients.notify(event))

    create_task(service_clients.store(event))

    create_task(service_clients.analyze(event))

    return event


@router.get("/detection")
async def get_detection_events():
    """
    Get all AI detection events.
    """

    return event_service.get_detection_events()


@router.get("/detection/{event_id}")
async def get_detection_event(
    event_id: str,
):
    """
    Get a single AI detection event.
    """

    event = event_service.get_detection_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Detection event not found",
        )

    return event
