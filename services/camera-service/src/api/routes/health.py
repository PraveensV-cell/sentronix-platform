from fastapi import APIRouter

from src.schemas.health import HealthResponse
from src.services.camera_connection_manager import (
    camera_connection_manager,
)
from src.services.camera_health_service import (
    camera_health_service,
)
from src.services.camera_service import (
    camera_service,
)
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
        "active_connections": camera_connection_manager.active_connections(),
    }


@router.get("/cameras")
def all_camera_health():
    """
    Health of all registered cameras.
    """

    return camera_health_service.all()


@router.get("/cameras/{camera_name}")
def camera_health(
    camera_name: str,
):
    """
    Health information for a specific camera.
    """

    return camera_health_service.get(
        camera_name,
    )
