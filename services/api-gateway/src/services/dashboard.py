from sqlalchemy.orm import Session

from src.services.analytics import AnalyticsService
from src.services.alert_analytics import AlertAnalyticsService
from src.services.recording_analytics import RecordingAnalyticsService
from src.services.ai_analytics import AIAnalyticsService
from src.services.camera_analytics import CameraAnalyticsService


class DashboardService:
    """
    Main Dashboard Service.

    Combines all analytics services into one response
    for the frontend dashboard.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.analytics = AnalyticsService(db)
        self.alerts = AlertAnalyticsService(db)
        self.recordings = RecordingAnalyticsService(db)
        self.ai = AIAnalyticsService(db)
        self.cameras = CameraAnalyticsService(db)

    # -------------------------------------------------
    # Complete Dashboard
    # -------------------------------------------------

    def get_dashboard(self):

        return {
            "analytics": self.analytics.get_dashboard_data(),
            "alerts": self.alerts.get_dashboard_data(),
            "recordings": self.recordings.get_dashboard_data(),
            "ai": self.ai.get_dashboard_data(),
            "cameras": self.cameras.get_dashboard_data(),
        }

    # -------------------------------------------------
    # Dashboard Summary
    # -------------------------------------------------

    def get_summary(self):

        return {
            "total_detections": self.analytics.total_detections(),
            "average_confidence": self.analytics.average_confidence(),
            "total_alerts": self.alerts.total_alerts(),
            "total_recordings": self.recordings.total_recordings(),
            "total_cameras": self.cameras.total_cameras(),
            "online_cameras": self.cameras.online_cameras(),
            "ai_status": self.ai.ai_status(),
        }

    # -------------------------------------------------
    # Detection Trend
    # -------------------------------------------------

    def get_detection_trend(self):

        return self.analytics.daily_trend()

    # -------------------------------------------------
    # Alert Trend
    # -------------------------------------------------

    def get_alert_trend(self):

        return self.alerts.daily_trend()

    # -------------------------------------------------
    # Recording Trend
    # -------------------------------------------------

    def get_recording_trend(self):

        return self.recordings.daily_trend()
