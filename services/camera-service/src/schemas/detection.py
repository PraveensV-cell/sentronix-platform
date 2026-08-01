from pydantic import BaseModel


class DetectionRequest(BaseModel):
    """
    Detection request.
    """

    camera_name: str


class DetectionResponse(BaseModel):
    """
    Detection response.
    """

    success: bool
    detections: list[dict]
