from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.analytics import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/")
def get_dashboard_analytics(
    db: Session = Depends(get_db),
):
    """
    Return complete analytics.
    """
    return AnalyticsService(db).get_dashboard_data()


@router.get("/detections")
def detections_by_label(
    db: Session = Depends(get_db),
):
    """
    Detection statistics by label.
    """
    return AnalyticsService(db).detections_by_label()


@router.get("/confidence")
def average_confidence(
    db: Session = Depends(get_db),
):
    """
    Average confidence.
    """
    return AnalyticsService(db).average_confidence()


@router.get("/cameras")
def camera_statistics(
    db: Session = Depends(get_db),
):
    """
    Camera statistics.
    """
    return AnalyticsService(db).camera_statistics()


@router.get("/hourly")
def hourly_trend(
    db: Session = Depends(get_db),
):
    """
    Hourly detection trend.
    """
    return AnalyticsService(db).hourly_trend()


@router.get("/daily")
def daily_trend(
    db: Session = Depends(get_db),
):
    """
    Daily detection trend.
    """
    return AnalyticsService(db).daily_trend()


@router.get("/range")
def date_range(
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """
    Analytics between two dates.
    """
    return AnalyticsService(db).date_range(
        start,
        end,
    )
