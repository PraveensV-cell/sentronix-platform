from datetime import datetime

from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog


class AuditLogRepository:
    """
    Handles Audit Log database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        audit_log: AuditLog,
    ) -> AuditLog:
        """
        Save a new audit log.
        """

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log

    def get_all(self):
        """
        Return all audit logs.
        """

        return self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()

    def get_by_id(
        self,
        audit_log_id: int,
    ):
        """
        Return audit log by ID.
        """

        return self.db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()

    def get_by_user(
        self,
        user_id: int,
    ):
        """
        Return all audit logs for a user.
        """

        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_by_action(
        self,
        action: str,
    ):
        """
        Return audit logs by action.
        """

        return (
            self.db.query(AuditLog)
            .filter(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_by_resource(
        self,
        resource: str,
    ):
        """
        Return audit logs by resource.
        """

        return (
            self.db.query(AuditLog)
            .filter(AuditLog.resource == resource)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def search(
        self,
        user_id: int | None = None,
        action: str | None = None,
        resource: str | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Advanced Audit Log Search.
        """

        query = self.db.query(AuditLog)

        if user_id is not None:
            query = query.filter(
                AuditLog.user_id == user_id,
            )

        if action:
            query = query.filter(
                AuditLog.action == action,
            )

        if resource:
            query = query.filter(
                AuditLog.resource == resource,
            )

        if ip_address:
            query = query.filter(
                AuditLog.ip_address == ip_address,
            )

        if start_date:
            query = query.filter(
                AuditLog.created_at >= start_date,
            )

        if end_date:
            query = query.filter(
                AuditLog.created_at <= end_date,
            )

        return query.order_by(
            AuditLog.created_at.desc(),
        ).all()

    def delete(
        self,
        audit_log: AuditLog,
    ):
        """
        Delete an audit log.
        """

        self.db.delete(audit_log)
        self.db.commit()
