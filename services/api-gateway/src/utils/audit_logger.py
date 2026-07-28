from sqlalchemy.orm import Session

from src.schemas.audit_log import AuditLogCreate
from src.services.audit_log import AuditLogService


class AuditLogger:
    """
    Utility class for writing audit logs.
    """

    @staticmethod
    def log(
        db: Session,
        action: str,
        resource: str,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
    ):
        """
        Create an audit log entry.
        """

        service = AuditLogService(db)

        return service.create_audit_log(
            AuditLogCreate(
                user_id=user_id,
                action=action,
                resource=resource,
                description=description,
                ip_address=ip_address,
            )
        )

    @staticmethod
    def login(
        db: Session,
        user_id: int,
        ip_address: str | None = None,
    ):
        """
        Log user login.
        """

        return AuditLogger.log(
            db=db,
            user_id=user_id,
            action="LOGIN",
            resource="Authentication",
            description="User logged into the system.",
            ip_address=ip_address,
        )

    @staticmethod
    def logout(
        db: Session,
        user_id: int,
        ip_address: str | None = None,
    ):
        """
        Log user logout.
        """

        return AuditLogger.log(
            db=db,
            user_id=user_id,
            action="LOGOUT",
            resource="Authentication",
            description="User logged out of the system.",
            ip_address=ip_address,
        )

    @staticmethod
    def create(
        db: Session,
        resource: str,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
    ):
        """
        Log create action.
        """

        return AuditLogger.log(
            db=db,
            user_id=user_id,
            action="CREATE",
            resource=resource,
            description=description,
            ip_address=ip_address,
        )

    @staticmethod
    def update(
        db: Session,
        resource: str,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
    ):
        """
        Log update action.
        """

        return AuditLogger.log(
            db=db,
            user_id=user_id,
            action="UPDATE",
            resource=resource,
            description=description,
            ip_address=ip_address,
        )

    @staticmethod
    def delete(
        db: Session,
        resource: str,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
    ):
        """
        Log delete action.
        """

        return AuditLogger.log(
            db=db,
            user_id=user_id,
            action="DELETE",
            resource=resource,
            description=description,
            ip_address=ip_address,
        )

    @staticmethod
    def view(
        db: Session,
        resource: str,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
    ):
        """
        Log view action.
        """

        return AuditLogger.log(
            db=db,
            user_id=user_id,
            action="VIEW",
            resource=resource,
            description=description,
            ip_address=ip_address,
        )


audit_logger = AuditLogger()
