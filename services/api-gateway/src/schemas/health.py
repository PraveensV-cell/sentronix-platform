from datetime import datetime

from pydantic import Field

from src.schemas.common import BaseResponse


class HealthResponse(BaseResponse):
    service: str = Field(...)
    status: str = Field(...)
    version: str = Field(...)

    uptime: str = Field(...)
    timestamp: datetime = Field(...)
