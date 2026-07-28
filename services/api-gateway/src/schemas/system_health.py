from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SystemHealthBase(BaseModel):
    """
    Base schema for system health.
    """

    cpu_usage: float = Field(..., ge=0, le=100)

    memory_usage: float = Field(..., ge=0, le=100)

    disk_usage: float = Field(..., ge=0, le=100)

    network_usage: float = Field(..., ge=0)

    uptime: str

    database_status: str

    ai_status: str


class SystemHealthCreate(SystemHealthBase):
    """
    Schema used when creating a health snapshot.
    """

    pass


class SystemHealthUpdate(BaseModel):
    """
    Schema used when updating a health snapshot.
    """

    cpu_usage: float | None = Field(default=None, ge=0, le=100)

    memory_usage: float | None = Field(default=None, ge=0, le=100)

    disk_usage: float | None = Field(default=None, ge=0, le=100)

    network_usage: float | None = Field(default=None, ge=0)

    uptime: str | None = None

    database_status: str | None = None

    ai_status: str | None = None


class SystemHealthResponse(SystemHealthBase):
    """
    Response schema.
    """

    id: int

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
