from pydantic import BaseModel


class ServiceResponse(BaseModel):
    name: str
    version: str
    environment: str
    status: str
