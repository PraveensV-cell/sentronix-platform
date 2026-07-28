from datetime import datetime

from pydantic import BaseModel


class EventCreate(BaseModel):
    event_type: str

    source: str

    description: str


class EventResponse(BaseModel):
    event_id: str

    event_type: str

    source: str

    description: str

    created_at: datetime
