from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RecordingBase(BaseModel):
    """
    Base Recording Schema.
    """

    camera_id: int = Field(..., gt=0)

    file_name: str

    file_path: str

    duration: float = 0.0

    size: float = 0.0

    start_time: datetime

    end_time: datetime


class RecordingCreate(RecordingBase):
    """
    Create Recording Schema.
    """

    pass


class RecordingUpdate(BaseModel):
    """
    Update Recording Schema.
    """

    duration: float | None = None

    size: float | None = None

    end_time: datetime | None = None


class RecordingResponse(RecordingBase):
    """
    Response Schema.
    """

    id: int

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
