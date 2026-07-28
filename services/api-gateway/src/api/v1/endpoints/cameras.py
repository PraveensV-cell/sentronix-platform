from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.schemas.camera import (
    CameraCreate,
    CameraResponse,
    CameraUpdate,
)
from src.services.camera import CameraService

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"],
)


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a Camera",
)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new surveillance camera.
    """

    service = CameraService(db)

    try:
        return service.create_camera(camera)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[CameraResponse],
    summary="List Cameras",
)
def list_cameras(
    db: Session = Depends(get_db),
):
    """
    Retrieve all registered cameras.
    """

    service = CameraService(db)

    return service.list_cameras()


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Get Camera",
)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a camera by its ID.
    """

    service = CameraService(db)

    camera = service.get_camera(camera_id)

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found.",
        )

    return camera


@router.put(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Update Camera",
)
def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: Session = Depends(get_db),
):
    """
    Update camera information.
    """

    service = CameraService(db)

    try:
        camera = service.update_camera(
            camera_id,
            camera_data,
        )

        if camera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found.",
            )

        return camera

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.delete(
    "/{camera_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Camera",
)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a registered camera.
    """

    service = CameraService(db)

    deleted = service.delete_camera(camera_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found.",
        )

    return {
        "success": True,
        "message": "Camera deleted successfully.",
    }


@router.post(
    "/{camera_id}/refresh",
    response_model=CameraResponse,
    summary="Refresh Camera Status",
)
def refresh_camera(
    camera_id: int,
    db: Session = Depends(get_db),
):
    """
    Refresh the online/offline status of a camera.
    """

    service = CameraService(db)

    camera = service.refresh_camera_status(camera_id)

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found.",
        )

    return camera
