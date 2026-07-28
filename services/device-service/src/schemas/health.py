from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Health check response.
    """

    service: str
    version: str
    status: str
    timestamp: datetime
