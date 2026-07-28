from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.schemas.detection import (
    DetectionCreate,
    DetectionResponse,
    DetectionUpdate,
)
from src.services.detection import DetectionService

router = APIRouter(
    prefix="/detections",
    tags=["Detections"],
)


@router.post(
    "",
    response_model=DetectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Detection",
)
def create_detection(
    detection: DetectionCreate,
    db: Session = Depends(get_db),
):
    """
    Save a new AI detection.
    """

    service = DetectionService(db)

    return service.create_detection(detection)


@router.get(
    "",
    response_model=list[DetectionResponse],
    summary="List Detections",
)
def list_detections(
    db: Session = Depends(get_db),
):
    """
    Return all detections.
    """

    service = DetectionService(db)

    return service.list_detections()


@router.get(
    "/{detection_id}",
    response_model=DetectionResponse,
    summary="Get Detection",
)
def get_detection(
    detection_id: int,
    db: Session = Depends(get_db),
):
    """
    Return one detection.
    """

    service = DetectionService(db)

    detection = service.get_detection(detection_id)

    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found.",
        )

    return detection


@router.put(
    "/{detection_id}",
    response_model=DetectionResponse,
    summary="Update Detection",
)
def update_detection(
    detection_id: int,
    detection_data: DetectionUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a detection.
    """

    service = DetectionService(db)

    detection = service.update_detection(
        detection_id,
        detection_data,
    )

    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found.",
        )

    return detection


@router.delete(
    "/{detection_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Detection",
)
def delete_detection(
    detection_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a detection.
    """

    service = DetectionService(db)

    deleted = service.delete_detection(
        detection_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found.",
        )

    return {
        "success": True,
        "message": "Detection deleted successfully.",
    }


@router.get(
    "/camera/{camera_id}",
    response_model=list[DetectionResponse],
    summary="Camera Detections",
)
def camera_detections(
    camera_id: int,
    db: Session = Depends(get_db),
):
    """
    Return detections for a camera.
    """

    service = DetectionService(db)

    return service.list_camera_detections(
        camera_id,
    )


@router.get(
    "/label/{label}",
    response_model=list[DetectionResponse],
    summary="Label Detections",
)
def label_detections(
    label: str,
    db: Session = Depends(get_db),
):
    """
    Return detections having a specific label.
    """

    service = DetectionService(db)

    return service.list_label_detections(
        label,
    )
