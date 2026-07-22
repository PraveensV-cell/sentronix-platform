from src.schemas.common import BaseResponse


class HealthResponse(BaseResponse):
    service: str
    status: str
    version: str
