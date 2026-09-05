from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Health response schema.
    """

    service: str

    version: str

    status: str

    timestamp: datetime
