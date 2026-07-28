from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from sqlalchemy.orm import Session

from src.database.session import get_db

from src.schemas.recording import (
    RecordingCreate,
    RecordingResponse,
    RecordingUpdate,
)

from src.services.recording import RecordingService


router = APIRouter(
    prefix="/recordings",
    tags=["Recordings"],
)


@router.post(
    "",
    response_model=RecordingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recording(
    recording: RecordingCreate,
    db: Session = Depends(get_db),
):

    return RecordingService(db).create_recording(recording)


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
            status_code=404,
            detail="Recording not found",
        )

    return recording


@router.put(
    "/{recording_id}",
    response_model=RecordingResponse,
)
def update_recording(
    recording_id: int,
    recording_data: RecordingUpdate,
    db: Session = Depends(get_db),
):

    recording = RecordingService(db).update_recording(
        recording_id,
        recording_data,
    )

    if recording is None:
        raise HTTPException(
            status_code=404,
            detail="Recording not found",
        )

    return recording


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
            status_code=404,
            detail="Recording not found",
        )

    return {
        "success": True,
        "message": "Recording deleted successfully",
    }
