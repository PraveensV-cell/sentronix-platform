from pydantic import BaseModel
from pydantic import Field


class CameraCreate(BaseModel):
    """
    Camera registration schema.
    """

    camera_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    camera_url: str

    location: str = Field(
        default="Unknown",
    )


class CameraStatus(BaseModel):
    """
    Camera status.
    """

    camera_name: str

    status: str

    fps: float

    is_recording: bool


class CameraResponse(BaseModel):
    camera_name: str

    camera_url: str

    location: str

    connected: bool
