from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.audit_log import AuditLogService

from datetime import datetime

from fastapi import Query

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get("/")
def list_audit_logs(
    db: Session = Depends(get_db),
):
    """
    Get all audit logs.
    """

    service = AuditLogService(db)

    return service.list_audit_logs()


@router.get("/{audit_log_id}")
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
):
    """
    Get audit log by ID.
    """

    service = AuditLogService(db)

    audit_log = service.get_audit_log(audit_log_id)

    if audit_log is None:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found.",
        )

    return audit_log


@router.get("/user/{user_id}")
def get_user_audit_logs(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get audit logs for a user.
    """

    service = AuditLogService(db)

    return service.get_user_audit_logs(user_id)


@router.get("/action/{action}")
def get_action_audit_logs(
    action: str,
    db: Session = Depends(get_db),
):
    """
    Get audit logs by action.
    """

    service = AuditLogService(db)

    return service.get_action_audit_logs(action)


@router.get("/resource/{resource}")
def get_resource_audit_logs(
    resource: str,
    db: Session = Depends(get_db),
):
    """
    Get audit logs by resource.
    """

    service = AuditLogService(db)

    return service.get_resource_audit_logs(resource)


@router.delete("/{audit_log_id}")
def delete_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an audit log.
    """

    service = AuditLogService(db)

    deleted = service.delete_audit_log(audit_log_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found.",
        )

    return {"message": "Audit log deleted successfully."}


@router.get("/search")
def search_audit_logs(
    user_id: int | None = None,
    action: str | None = None,
    resource: str | None = None,
    ip_address: str | None = None,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Search audit logs using filters.
    """

    service = AuditLogService(db)

    return service.search_audit_logs(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date,
    )
