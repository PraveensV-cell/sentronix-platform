from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertBase(BaseModel):
    """
    Base Alert Schema.
    """

    camera_id: int = Field(..., gt=0)
    detection_id: int = Field(..., gt=0)

    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    message: str

    severity: str = Field(
        default="INFO",
    )

    status: str = Field(
        default="OPEN",
    )


class AlertCreate(AlertBase):
    """
    Create Alert Schema.
    """

    pass


class AlertUpdate(BaseModel):
    """
    Update Alert Schema.
    """

    status: str | None = None


class AlertResponse(AlertBase):
    """
    Response Schema.
    """

    id: int

    created_at: datetime

    acknowledged_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
