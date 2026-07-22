from pydantic import Field

from src.schemas.common import BaseRequest, BaseResponse


class LoginRequest(BaseRequest):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class TokenResponse(BaseResponse):
    access_token: str
    token_type: str
