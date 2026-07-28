from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    events: int

    detections: int

    cameras: int

    devices: int

    storage_gb: float


# ==========================================================
# Detection Event
# ==========================================================


class AnalyticsEventRequest(BaseModel):
    event_id: str

    event_type: str

    camera_id: int

    detections: list[dict[str, Any]]

    created_at: datetime
