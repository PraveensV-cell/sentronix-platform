from datetime import datetime

from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog
from src.repositories.audit_log_repository import AuditLogRepository
from src.schemas.audit_log import AuditLogCreate


class AuditLogService:
    """
    Business logic for audit logs.
    """

    def __init__(self, db: Session):
        self.repository = AuditLogRepository(db)

    def create_audit_log(
        self,
        audit_log_data: AuditLogCreate,
    ) -> AuditLog:
        """
        Create a new audit log.
        """

        audit_log = AuditLog(
            user_id=audit_log_data.user_id,
            action=audit_log_data.action,
            resource=audit_log_data.resource,
            description=audit_log_data.description,
            ip_address=audit_log_data.ip_address,
        )

        return self.repository.create(audit_log)

    def list_audit_logs(self):
        """
        Return all audit logs.
        """

        return self.repository.get_all()

    def get_audit_log(
        self,
        audit_log_id: int,
    ):
        """
        Return an audit log by ID.
        """

        return self.repository.get_by_id(audit_log_id)

    def get_user_audit_logs(
        self,
        user_id: int,
    ):
        """
        Return audit logs for a specific user.
        """

        return self.repository.get_by_user(user_id)

    def get_action_audit_logs(
        self,
        action: str,
    ):
        """
        Return audit logs by action.
        """

        return self.repository.get_by_action(action)

    def get_resource_audit_logs(
        self,
        resource: str,
    ):
        """
        Return audit logs by resource.
        """

        return self.repository.get_by_resource(resource)

    def search_audit_logs(
        self,
        user_id: int | None = None,
        action: str | None = None,
        resource: str | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Search audit logs using multiple filters.
        """

        return self.repository.search(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            start_date=start_date,
            end_date=end_date,
        )

    def delete_audit_log(
        self,
        audit_log_id: int,
    ) -> bool:
        """
        Delete an audit log.
        """

        audit_log = self.repository.get_by_id(audit_log_id)

        if audit_log is None:
            return False

        self.repository.delete(audit_log)

        return True
