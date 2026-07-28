from fastapi import APIRouter

from src.schemas.health import HealthResponse
from src.services.camera_service import camera_service
from src.services.camera_stream_service import (
    camera_stream_service,
)
from src.services.recording_service import (
    recording_service,
)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "/",
    response_model=HealthResponse,
)
def service_health():
    """
    Camera Service health.
    """

    return HealthResponse(
        service="Camera Service",
        status="Healthy",
        cameras=len(
            camera_service.cameras,
        ),
        active_streams=camera_stream_service.active_count(),
    )


@router.get("/details")
def health_details():
    """
    Detailed service status.
    """

    return {
        "service": "Camera Service",
        "status": "Healthy",
        "registered_cameras": len(
            camera_service.cameras,
        ),
        "active_streams": camera_stream_service.active_count(),
        "active_recordings": recording_service.active_recordings(),
    }
