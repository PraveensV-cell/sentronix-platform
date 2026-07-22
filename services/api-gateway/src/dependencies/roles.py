from fastapi import Depends, HTTPException, status

from src.dependencies.auth import get_current_user


class RoleChecker:
    """
    Role-Based Access Control dependency.
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user=Depends(get_current_user),
    ):
        role = current_user.get("role")

        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user
