from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.schemas.recording import RecordingResponse
from src.services.recording import RecordingService

router = APIRouter(
    prefix="/recordings",
    tags=["Recordings"],
)


@router.get(
    "",
    response_model=list[RecordingResponse],
)
def list_recordings(
    db: Session = Depends(get_db),
):

    return RecordingService(db).list_recordings()


@router.get(
    "/{recording_id}",
    response_model=RecordingResponse,
)
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db),
):

    recording = RecordingService(db).get_recording(recording_id)

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    return recording


@router.get(
    "/camera/{camera_id}",
    response_model=list[RecordingResponse],
)
def camera_recordings(
    camera_id: int,
    db: Session = Depends(get_db),
):

    return RecordingService(db).get_camera_recordings(camera_id)


@router.delete(
    "/{recording_id}",
)
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
):

    deleted = RecordingService(db).delete_recording(recording_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    return {
        "success": True,
        "message": "Recording deleted successfully",
    }
