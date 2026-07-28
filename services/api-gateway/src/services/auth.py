from sqlalchemy.orm import Session

from src.auth.jwt import create_access_token
from src.auth.password import verify_password
from src.schemas.auth import TokenResponse
from src.services.user import UserService


class AuthenticationService:
    """
    Handles user authentication.
    """

    def __init__(self, db: Session):
        self.user_service = UserService(db)

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> TokenResponse | None:

        user = self.user_service.authenticate_user(username)

        if user is None:
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        access_token = create_access_token(
            {
                "sub": user.username,
                "role": user.role,
            }
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
