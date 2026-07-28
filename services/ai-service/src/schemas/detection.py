from pydantic import BaseModel


class DetectionRequest(BaseModel):
    image_path: str


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: list[int]


class DetectionResponse(BaseModel):
    success: bool
    detections: list[Detection]
