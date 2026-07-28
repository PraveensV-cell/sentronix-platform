from fastapi import APIRouter

from src.services.live_detection_service import LiveDetectionService

router = APIRouter(
    prefix="/detect",
    tags=["Live Detection"],
)


@router.get("/live")
def live_detection():
    """
    Start webcam detection.
    """

    service = LiveDetectionService()

    return service.start(0)
