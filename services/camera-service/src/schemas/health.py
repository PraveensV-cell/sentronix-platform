from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str

    status: str

    cameras: int

    active_streams: int
