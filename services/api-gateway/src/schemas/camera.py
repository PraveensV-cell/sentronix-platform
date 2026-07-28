from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CameraCreate(BaseModel):
    """
    Schema for creating a camera.
    """

    name: str
    location: str
    rtsp_url: str
    camera_type: str = "rtsp"
    zone: str = "Default"


class CameraUpdate(BaseModel):
    """
    Schema for updating a camera.
    """

    name: str | None = None
    location: str | None = None
    rtsp_url: str | None = None
    camera_type: str | None = None
    zone: str | None = None
    status: str | None = None
    is_active: bool | None = None


class CameraResponse(BaseModel):
    """
    Camera response schema.
    """

    id: int
    name: str
    location: str
    rtsp_url: str
    camera_type: str
    zone: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
