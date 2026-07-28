from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: str
