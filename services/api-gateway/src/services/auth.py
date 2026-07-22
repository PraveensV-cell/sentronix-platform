from src.core.jwt import create_access_token
from src.core.security import verify_password


class AuthenticationService:
    """
    Enterprise Authentication Service
    """

    def authenticate(
        self,
        username: str,
        password: str,
    ):
        """
        Authenticate a user.

        NOTE:
        Temporary hardcoded credentials.
        Database integration comes later.
        """

        demo_username = "admin"
        demo_password = "Sentronix@123"

        if username != demo_username:
            return None

        # Temporary hash generation.
        # This will be replaced by database lookup later.
        from src.core.security import hash_password

        hashed_password = hash_password(demo_password)

        if not verify_password(password, hashed_password):
            return None

        token = create_access_token(
            {
                "sub": username,
                "role": "super_admin",
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }
