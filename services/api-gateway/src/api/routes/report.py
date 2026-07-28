from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.reports.csv_generator import CSVGenerator
from src.reports.excel_generator import ExcelGenerator
from src.reports.pdf_generator import PDFGenerator
from src.schemas.report import ReportCreate
from src.services.alert import AlertService
from src.services.detection import DetectionService
from src.services.recording import RecordingService
from src.services.report import ReportService

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def reports_directory() -> Path:
    path = Path("storage") / "reports"
    path.mkdir(
        parents=True,
        exist_ok=True,
    )
    return path


# ---------------------------------------------------
# Detection Reports
# ---------------------------------------------------


@router.post("/detections/pdf")
def detection_pdf(
    generated_by: int,
    db: Session = Depends(get_db),
):
    detections = DetectionService(db).list_detections()

    file_name = f"detections_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    file_path = reports_directory() / file_name

    PDFGenerator().generate_detection_report(
        detections,
        str(file_path),
    )

    report = ReportService(db).create_report(
        ReportCreate(
            report_type="Detection PDF",
            file_name=file_name,
            file_path=str(file_path),
            generated_by=generated_by,
        )
    )

    return report


@router.post("/detections/csv")
def detection_csv(
    generated_by: int,
    db: Session = Depends(get_db),
):
    detections = DetectionService(db).list_detections()

    file_name = f"detections_{datetime.now():%Y%m%d_%H%M%S}.csv"

    file_path = reports_directory() / file_name

    CSVGenerator().generate_detection_report(
        detections,
        str(file_path),
    )

    report = ReportService(db).create_report(
        ReportCreate(
            report_type="Detection CSV",
            file_name=file_name,
            file_path=str(file_path),
            generated_by=generated_by,
        )
    )

    return report


@router.post("/detections/excel")
def detection_excel(
    generated_by: int,
    db: Session = Depends(get_db),
):
    detections = DetectionService(db).list_detections()

    file_name = f"detections_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

    file_path = reports_directory() / file_name

    ExcelGenerator().generate_detection_report(
        detections,
        str(file_path),
    )

    report = ReportService(db).create_report(
        ReportCreate(
            report_type="Detection Excel",
            file_name=file_name,
            file_path=str(file_path),
            generated_by=generated_by,
        )
    )

    return report


# ---------------------------------------------------
# Alert Reports
# ---------------------------------------------------


@router.post("/alerts/pdf")
def alert_pdf(
    generated_by: int,
    db: Session = Depends(get_db),
):
    alerts = AlertService(db).list_alerts()

    file_name = f"alerts_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    file_path = reports_directory() / file_name

    PDFGenerator().generate_alert_report(
        alerts,
        str(file_path),
    )

    report = ReportService(db).create_report(
        ReportCreate(
            report_type="Alert PDF",
            file_name=file_name,
            file_path=str(file_path),
            generated_by=generated_by,
        )
    )

    return report


# ---------------------------------------------------
# Recording Reports
# ---------------------------------------------------


@router.post("/recordings/pdf")
def recording_pdf(
    generated_by: int,
    db: Session = Depends(get_db),
):
    recordings = RecordingService(db).list_recordings()

    file_name = f"recordings_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    file_path = reports_directory() / file_name

    PDFGenerator().generate_recording_report(
        recordings,
        str(file_path),
    )

    report = ReportService(db).create_report(
        ReportCreate(
            report_type="Recording PDF",
            file_name=file_name,
            file_path=str(file_path),
            generated_by=generated_by,
        )
    )

    return report


# ---------------------------------------------------
# Report Management
# ---------------------------------------------------


@router.get("/")
def list_reports(
    db: Session = Depends(get_db),
):
    return ReportService(db).list_reports()


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = ReportService(db).get_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return FileResponse(
        report.file_path,
        filename=report.file_name,
    )


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    deleted = ReportService(db).delete_report(report_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return {"message": "Report deleted successfully."}
