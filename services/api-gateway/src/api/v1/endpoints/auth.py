from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.schemas.auth import LoginRequest, TokenResponse
from src.services.auth import AuthenticationService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# Role Dependency
admin_only = RoleChecker(["super_admin"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user using the PostgreSQL database
    and return a JWT access token.
    """

    auth_service = AuthenticationService(db)

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
    summary="Current Logged-in User",
)
async def get_me(
    current_user=Depends(get_current_user),
):
    """
    Return information about the currently authenticated user.
    """

    return {
        "success": True,
        "user": current_user,
    }


@router.get(
    "/admin",
    summary="Admin Panel",
)
async def admin_panel(
    current_user=Depends(admin_only),
):
    """
    Accessible only to users with the 'super_admin' role.
    """

    return {
        "success": True,
        "message": "Welcome to the SENTRONIX Admin Panel",
        "user": current_user,
    }
