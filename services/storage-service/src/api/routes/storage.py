from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.core.config import settings
from src.schemas.health import HealthResponse
from src.schemas.storage import (
    StorageResponse,
    StorageEventRequest,
    EvidenceCreate,
)
from src.services.storage_service import StorageService

router = APIRouter()
storage_service = StorageService()


@router.get("/", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.get("/ping")
async def ping():
    return {"message": "pong"}


# ==========================================================
# Detection Event Storage
# ==========================================================


@router.post("/events")
async def receive_event(
    event: StorageEventRequest,
):
    """
    Receive AI detection event.
    """
    return storage_service.store_event(event)


@router.get("/events")
async def get_events():
    """
    Return stored detection events.
    """
    return storage_service.get_event_files()


# ==========================================================
# File Storage
# ==========================================================


@router.get(
    "/files",
    response_model=list[StorageResponse],
)
async def get_files():
    """
    Return all stored files.
    """
    return storage_service.get_all()


@router.get(
    "/files/{file_id}",
    response_model=StorageResponse,
)
async def get_file(file_id: str):

    file = storage_service.get(file_id)

    if file is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return file


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):

    success = storage_service.delete(file_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return {
        "message": "File deleted successfully",
    }


# ==========================================================
# Evidence
# ==========================================================


@router.post(
    "/evidence",
    response_model=StorageResponse,
)
async def register_evidence(
    request: EvidenceCreate,
):

    return storage_service.register_evidence(
        filename=request.filename,
        category=request.category,
    )


@router.get("/evidence")
async def evidence():

    files = storage_service.get_all()

    return [
        file
        for file in files
        if file.category
        in (
            "image",
            "snapshot",
            "video",
        )
    ]
