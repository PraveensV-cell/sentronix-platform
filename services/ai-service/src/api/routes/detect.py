from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException
from loguru import logger

from src.schemas.detection import (
    DetectionRequest,
    DetectionResponse,
)

from src.services.detection_service import (
    detection_service,
)

from src.services.event_client import (
    event_client,
)


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
    """
    Run AI detection on image.
    """

    try:
        result = detection_service.detect_image(
            request.image_path,
        )

        detections = result.get(
            "detections",
            [],
        )

        try:
            await event_client.publish_detection(
                camera_id=0,
                detections=detections,
            )

            logger.info(
                "Detection event published successfully.",
            )

        except Exception as exc:
            logger.warning(
                f"Detection event publish failed: {exc}",
            )

        return DetectionResponse(
            success=True,
            detections=detections,
            annotated_image=result.get(
                "annotated_image",
            ),
            total_objects=len(
                detections,
            ),
        )

    except Exception as exc:
        logger.error(
            f"Detection failed: {exc}",
        )

        raise HTTPException(
            status_code=500,
            detail="Detection failed.",
        )
