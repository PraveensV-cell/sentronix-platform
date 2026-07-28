from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AuditLogBase(BaseModel):
    """
    Base Audit Log Schema.
    """

    user_id: int | None = None

    action: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    resource: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        ...,
        min_length=1,
    )

    ip_address: str | None = None


class AuditLogCreate(AuditLogBase):
    """
    Schema used to create an audit log.
    """

    pass


class AuditLogUpdate(BaseModel):
    """
    Schema used to update an audit log.
    """

    action: str | None = None

    resource: str | None = None

    description: str | None = None

    ip_address: str | None = None


class AuditLogResponse(AuditLogBase):
    """
    Schema returned from API.
    """

    id: int

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
