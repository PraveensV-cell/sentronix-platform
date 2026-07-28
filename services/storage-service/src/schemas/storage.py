from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StorageCreate(BaseModel):
    filename: str
    category: str
    path: str
    size: int


class StorageResponse(BaseModel):
    file_id: str
    filename: str
    category: str
    path: str
    size: int
    uploaded_at: datetime


# ==========================================================
# Detection Event Storage
# ==========================================================


class StorageEventRequest(BaseModel):
    event_id: str
    event_type: str
    camera_id: int
    detections: list[dict[str, Any]]
    created_at: datetime


# ==========================================================
# Evidence
# ==========================================================


class EvidenceCreate(BaseModel):
    filename: str
    category: str
