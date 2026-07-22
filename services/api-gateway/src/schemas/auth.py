from pydantic import Field

from src.schemas.common import BaseRequest


class LoginRequest(BaseRequest):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )
