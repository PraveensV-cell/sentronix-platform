from fastapi import APIRouter
from fastapi import HTTPException

from src.schemas.camera import CameraCreate
from src.services.camera_service import camera_service
from src.services.recording_service import recording_service

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"],
)


@router.post("/")
def register_camera(
    camera: CameraCreate,
):
    """
    Register a new camera.
    """

    return camera_service.register_camera(
        camera,
    )


@router.get("/")
def list_cameras():
    """
    List all registered cameras.
    """

    return camera_service.get_all_cameras()


@router.get("/{camera_name}")
def get_camera(
    camera_name: str,
):
    """
    Get one camera.
    """

    camera = camera_service.get_camera(
        camera_name,
    )

    if camera is None:
        raise HTTPException(
            status_code=404,
            detail="Camera not found.",
        )

    return camera


@router.delete("/{camera_name}")
def delete_camera(
    camera_name: str,
):
    """
    Remove camera.
    """

    deleted = camera_service.remove_camera(
        camera_name,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Camera not found.",
        )

    return {
        "message": "Camera removed successfully.",
    }


@router.get("/{camera_name}/status")
def camera_status(
    camera_name: str,
):
    """
    Camera status.
    """

    status = camera_service.camera_status(
        camera_name,
    )

    if status is None:
        raise HTTPException(
            status_code=404,
            detail="Camera not found.",
        )

    return status


@router.post("/{camera_name}/record/start")
def start_recording(
    camera_name: str,
):
    """
    Start recording.
    """

    return recording_service.start_recording(
        camera_name,
    )


@router.post("/{camera_name}/record/stop")
def stop_recording(
    camera_name: str,
):
    """
    Stop recording.
    """

    return recording_service.stop_recording(
        camera_name,
    )
