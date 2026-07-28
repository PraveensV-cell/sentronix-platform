from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.audit.csv_exporter import AuditCSVExporter
from src.audit.excel_exporter import AuditExcelExporter
from src.audit.pdf_exporter import AuditPDFExporter
from src.database.session import get_db
from src.services.audit_log import AuditLogService

router = APIRouter(
    prefix="/audit-logs/export",
    tags=["Audit Export"],
)


@router.get("/csv")
def export_csv(
    db: Session = Depends(get_db),
):
    """
    Export audit logs as CSV.
    """

    logs = AuditLogService(db).list_audit_logs()

    exporter = AuditCSVExporter()

    filepath = exporter.export(logs)

    return FileResponse(
        filepath,
        filename="audit_logs.csv",
        media_type="text/csv",
    )


@router.get("/excel")
def export_excel(
    db: Session = Depends(get_db),
):
    """
    Export audit logs as Excel.
    """

    logs = AuditLogService(db).list_audit_logs()

    exporter = AuditExcelExporter()

    filepath = exporter.export(logs)

    return FileResponse(
        filepath,
        filename="audit_logs.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


@router.get("/pdf")
def export_pdf(
    db: Session = Depends(get_db),
):
    """
    Export audit logs as PDF.
    """

    logs = AuditLogService(db).list_audit_logs()

    exporter = AuditPDFExporter()

    filepath = exporter.export(logs)

    return FileResponse(
        filepath,
        filename="audit_logs.pdf",
        media_type="application/pdf",
    )
