from fastapi import APIRouter, HTTPException, status

from src.schemas.auth import LoginRequest, TokenResponse
from src.services.auth import AuthenticationService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthenticationService()


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(request: LoginRequest):

    result = auth_service.authenticate(
        request.username,
        request.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return result
