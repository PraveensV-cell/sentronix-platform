from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.dashboard import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
):
    """
    Return complete dashboard.
    """

    return DashboardService(db).get_dashboard()


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
):
    """
    Return dashboard summary.
    """

    return DashboardService(db).get_summary()


@router.get("/detections")
def get_detection_trend(
    db: Session = Depends(get_db),
):
    """
    Detection analytics.
    """

    return DashboardService(db).get_detection_trend()


@router.get("/alerts")
def get_alert_trend(
    db: Session = Depends(get_db),
):
    """
    Alert analytics.
    """

    return DashboardService(db).get_alert_trend()


@router.get("/recordings")
def get_recording_trend(
    db: Session = Depends(get_db),
):
    """
    Recording analytics.
    """

    return DashboardService(db).get_recording_trend()
