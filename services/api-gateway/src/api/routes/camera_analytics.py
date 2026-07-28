from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.camera_analytics import CameraAnalyticsService

router = APIRouter(
    prefix="/camera-analytics",
    tags=["Camera Analytics"],
)


@router.get("/")
def get_camera_dashboard(
    db: Session = Depends(get_db),
):
    """
    Complete camera analytics dashboard.
    """

    return CameraAnalyticsService(db).get_dashboard_data()


@router.get("/summary")
def get_camera_summary(
    db: Session = Depends(get_db),
):
    """
    Camera summary.
    """

    service = CameraAnalyticsService(db)

    return {
        "total_cameras": service.total_cameras(),
        "online_cameras": service.online_cameras(),
        "offline_cameras": service.offline_cameras(),
        "active_cameras": service.active_cameras(),
    }


@router.get("/utilization")
def get_camera_utilization(
    db: Session = Depends(get_db),
):
    """
    Camera utilization statistics.
    """

    return CameraAnalyticsService(db).camera_utilization()


@router.get("/detections")
def get_detection_statistics(
    db: Session = Depends(get_db),
):
    """
    Detection count per camera.
    """

    return CameraAnalyticsService(db).detections_per_camera()


@router.get("/alerts")
def get_alert_statistics(
    db: Session = Depends(get_db),
):
    """
    Alert count per camera.
    """

    return CameraAnalyticsService(db).alerts_per_camera()


@router.get("/recordings")
def get_recording_statistics(
    db: Session = Depends(get_db),
):
    """
    Recording count per camera.
    """

    return CameraAnalyticsService(db).recordings_per_camera()
