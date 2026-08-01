from __future__ import annotations

from pydantic import BaseModel, Field


class DetectionRequest(BaseModel):
    """
    Detection request schema.
    """

    image_path: str


class BoundingBox(BaseModel):
    """
    Bounding box coordinates.
    """

    x1: int
    y1: int
    x2: int
    y2: int


class Detection(BaseModel):
    """
    Single detected object.
    """

    class_id: int | None = None

    label: str

    confidence: float = Field(
        ge=0,
        le=1,
    )

    bbox: list[float] = Field(
        default_factory=list,
    )


class DetectionResponse(BaseModel):
    """
    Detection API response.
    """

    success: bool

    detections: list[Detection] = Field(
        default_factory=list,
    )

    annotated_image: str | None = None

    total_objects: int = 0


class BatchDetectionRequest(BaseModel):
    """
    Batch detection request.
    """

    images: list[str] = Field(
        default_factory=list,
    )


class BatchDetectionResponse(BaseModel):
    """
    Batch detection response.
    """

    success: bool

    results: list[DetectionResponse] = Field(
        default_factory=list,
    )


class LiveDetectionResponse(BaseModel):
    """
    Live detection response.
    """

    camera: str

    detections: list[Detection] = Field(
        default_factory=list,
    )

    timestamp: str | None = None
