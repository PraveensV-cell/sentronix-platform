from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.ai_analytics import AIAnalyticsService

router = APIRouter(
    prefix="/ai-analytics",
    tags=["AI Analytics"],
)


@router.get("/")
def get_ai_dashboard(
    db: Session = Depends(get_db),
):
    """
    Complete AI analytics.
    """

    return AIAnalyticsService(db).get_dashboard_data()


@router.get("/status")
def get_ai_status(
    db: Session = Depends(get_db),
):
    """
    AI model status.
    """

    service = AIAnalyticsService(db)

    return {
        "status": service.ai_status(),
    }


@router.get("/confidence")
def get_confidence_statistics(
    db: Session = Depends(get_db),
):
    """
    AI confidence statistics.
    """

    service = AIAnalyticsService(db)

    return {
        "average_confidence": service.average_confidence(),
        "highest_confidence": service.highest_confidence(),
        "lowest_confidence": service.lowest_confidence(),
    }


@router.get("/resources")
def get_resource_usage(
    db: Session = Depends(get_db),
):
    """
    CPU / Memory / Disk / Network usage.
    """

    service = AIAnalyticsService(db)

    return {
        "cpu_usage": service.cpu_usage(),
        "memory_usage": service.memory_usage(),
        "disk_usage": service.disk_usage(),
        "network_usage": service.network_usage(),
    }


@router.get("/labels")
def get_detection_labels(
    db: Session = Depends(get_db),
):
    """
    Detection labels.
    """

    return AIAnalyticsService(db).detection_labels()
