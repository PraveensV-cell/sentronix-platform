from sqlalchemy.orm import Session

from src.auth.password import hash_password
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate


class UserService:
    """
    Business logic for user management.
    """

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        """

        existing_username = self.repository.get_by_username(user_data.username)

        if existing_username:
            raise ValueError("Username already exists.")

        existing_email = self.repository.get_by_email(user_data.email)

        if existing_email:
            raise ValueError("Email already exists.")

        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            is_active=True,
        )

        return self.repository.create(user)

    def get_user_by_username(
        self,
        username: str,
    ) -> User | None:

        return self.repository.get_by_username(username)

    def get_user_by_id(
        self,
        user_id: int,
    ) -> User | None:

        return self.repository.get_by_id(user_id)

    def list_users(self):

        return self.repository.list_all()

    def delete_user(
        self,
        user_id: int,
    ) -> bool:

        user = self.repository.get_by_id(user_id)

        if not user:
            return False

        self.repository.delete(user)

        return True

    def authenticate_user(
        self,
        username: str,
    ):

        return self.repository.get_by_username(username)
