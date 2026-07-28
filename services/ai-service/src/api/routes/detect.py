from fastapi import APIRouter
from loguru import logger

from src.schemas.detection import DetectionRequest
from src.schemas.detection import DetectionResponse
from src.services.detector import detector
from src.services.event_client import event_client

router = APIRouter(
    prefix="/detect",
    tags=["AI Detection"],
)


@router.post(
    "",
    response_model=DetectionResponse,
)
async def detect(
    request: DetectionRequest,
):

    detections = detector.detect(
        request.image_path,
    )

    try:
        await event_client.publish_detection(
            camera_id=0,
            detections=detections,
        )

        logger.info("Detection event published successfully.")

    except Exception as exc:
        logger.warning(f"Failed to publish detection event: {exc}")

    return DetectionResponse(
        success=True,
        detections=detections,
    )
