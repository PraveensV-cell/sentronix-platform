from fastapi import APIRouter
from fastapi import HTTPException

from src.schemas.camera import CameraCreate
from src.services.camera_connection_manager import (
    camera_connection_manager,
)
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


@router.get("/{camera_name}/connection")
def camera_connection(
    camera_name: str,
):
    """
    Camera connection information.
    """

    return camera_connection_manager.connection_info(
        camera_name,
    )


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


@router.get("/recordings/active")
def active_recordings():
    """
    Get active recordings.
    """

    return recording_service.active_metadata()


@router.get("/recordings/history")
def recording_history():
    """
    Get recording history.
    """

    return recording_service.history()


@router.get("/{camera_name}/recording")
def recording_information(
    camera_name: str,
):
    """
    Get recording information.
    """

    info = recording_service.recording_info(
        camera_name,
    )

    if info is None:
        raise HTTPException(
            status_code=404,
            detail="Recording not found.",
        )

    return info


@router.get("/connections/usb")
def discover_usb_cameras():
    """
    Discover available USB cameras.
    """

    return camera_connection_manager.discover_usb_cameras()


@router.get("/connections")
def connection_statistics():
    """
    Camera connection statistics.
    """

    return camera_connection_manager.connection_count()
