from fastapi import APIRouter, HTTPException, status

from src.schemas.auth import LoginRequest, TokenResponse
from src.services.auth import AuthenticationService
from fastapi import Depends
from src.dependencies.roles import RoleChecker
from src.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthenticationService()
admin_only = RoleChecker(["super_admin"])


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


@router.get(
    "/me",
)
async def get_me(
    current_user=Depends(get_current_user),
):

    return {"user": current_user}


@router.get(
    "/admin",
)
async def admin_panel(
    current_user=Depends(admin_only),
):
    """
    Accessible only to super administrators.
    """

    return {
        "message": "Welcome to the SENTRONIX Admin Panel",
        "user": current_user,
    }
