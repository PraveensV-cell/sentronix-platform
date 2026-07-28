from fastapi import APIRouter
from fastapi import HTTPException

from src.services.camera_service import camera_service
from src.services.camera_stream_service import camera_stream_service

router = APIRouter(
    prefix="/stream",
    tags=["Streaming"],
)


@router.get("/{camera_name}")
def stream_camera(
    camera_name: str,
):
    """
    Live MJPEG stream.
    """

    camera = camera_service.get_camera(
        camera_name,
    )

    if camera is None:
        raise HTTPException(
            status_code=404,
            detail="Camera not found.",
        )

    return camera_stream_service.stream(
        camera_name,
    )


@router.post("/{camera_name}/stop")
def stop_stream(
    camera_name: str,
):
    """
    Stop live stream.
    """

    stopped = camera_stream_service.stop_stream(
        camera_name,
    )

    if not stopped:
        raise HTTPException(
            status_code=404,
            detail="Stream not running.",
        )

    return {
        "message": "Stream stopped successfully.",
    }


@router.get("/active/count")
def active_streams():
    """
    Number of active streams.
    """

    return {
        "active_streams": camera_stream_service.active_count(),
    }
