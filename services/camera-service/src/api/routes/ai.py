from fastapi import APIRouter
from fastapi import HTTPException

from src.services.ai_client import ai_client
from src.services.frame_buffer import frame_buffer

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post("/detect/{camera_name}")
def detect(
    camera_name: str,
):
    """
    Run AI detection.
    """

    frame = frame_buffer.get(
        camera_name,
    )

    if frame is None:
        raise HTTPException(
            status_code=404,
            detail="No frame available.",
        )

    return ai_client.detect(
        frame,
    )
