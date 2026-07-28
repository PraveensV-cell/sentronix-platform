from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DetectionBase(BaseModel):
    """
    Base Detection Schema
    """

    camera_id: int = Field(
        ...,
        gt=0,
        description="Camera ID",
    )

    label: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Detected object label",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence",
    )

    x1: int
    y1: int
    x2: int
    y2: int


class DetectionCreate(DetectionBase):
    """
    Schema used when creating a detection.
    """

    pass


class DetectionUpdate(BaseModel):
    """
    Schema used for updating detection.
    """

    label: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class DetectionResponse(DetectionBase):
    """
    Schema returned to clients.
    """

    id: int
    detected_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DetectionListResponse(BaseModel):
    """
    List of detections.
    """

    success: bool = True
    total: int
    detections: list[DetectionResponse]
