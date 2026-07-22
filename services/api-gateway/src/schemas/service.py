from src.schemas.common import BaseResponse


class ServiceResponse(BaseResponse):
    name: str
    version: str
    environment: str
    status: str
