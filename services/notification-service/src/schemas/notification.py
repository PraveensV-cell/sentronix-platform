from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    recipient: str
    subject: str
    message: str
    channel: str


class NotificationResponse(BaseModel):
    notification_id: str
    recipient: str
    subject: str
    message: str
    channel: str
    status: str
    created_at: datetime


# ==========================================================
# Event Notification
# ==========================================================


class EventNotificationRequest(BaseModel):
    event_id: str
    event_type: str
    camera_id: int
    created_at: datetime


# ==========================================================
# Detection Event Notification
# ==========================================================


class DetectionNotificationRequest(BaseModel):
    event_id: str
    event_type: str
    camera_id: int
    detections: list[dict[str, Any]]
    created_at: datetime
