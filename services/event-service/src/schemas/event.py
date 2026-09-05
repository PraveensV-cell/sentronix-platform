from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DetectionData(BaseModel):
    """
    AI detection information.
    """

    label: str

    confidence: float = Field(
        ge=0,
        le=1,
    )

    bbox: list[float] = Field(
        default_factory=list,
    )


class DetectionEventCreate(BaseModel):
    """
    Detection event received from AI service.
    """

    camera_id: int

    detections: list[DetectionData] = Field(
        default_factory=list,
    )


class CameraEventCreate(BaseModel):
    """
    Camera status event.
    """

    camera_id: int

    event: str

    timestamp: datetime | None = None


class EventCreate(BaseModel):
    """
    Generic event creation schema.
    """

    event_type: str

    source: str

    description: str

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class EventResponse(BaseModel):
    """
    Event response schema.
    """

    event_id: str

    event_type: str

    source: str

    description: str

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime
