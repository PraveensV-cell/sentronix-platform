from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.detection import Detection
from src.models.system_health import SystemHealth


class AIAnalyticsService:
    """
    AI Analytics Service.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # -----------------------------------------
    # Total AI Detections
    # -----------------------------------------

    def total_detections(self):

        return self.db.query(Detection).count()

    # -----------------------------------------
    # Average Confidence
    # -----------------------------------------

    def average_confidence(self):

        value = self.db.query(
            func.avg(
                Detection.confidence,
            )
        ).scalar()

        return round(
            float(value or 0),
            2,
        )

    # -----------------------------------------
    # Highest Confidence
    # -----------------------------------------

    def highest_confidence(self):

        value = self.db.query(
            func.max(
                Detection.confidence,
            )
        ).scalar()

        return round(
            float(value or 0),
            2,
        )

    # -----------------------------------------
    # Lowest Confidence
    # -----------------------------------------

    def lowest_confidence(self):

        value = self.db.query(
            func.min(
                Detection.confidence,
            )
        ).scalar()

        return round(
            float(value or 0),
            2,
        )

    # -----------------------------------------
    # AI Status
    # -----------------------------------------

    def ai_status(self):

        latest = (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).first()
        )

        if latest is None:
            return "UNKNOWN"

        return latest.ai_status

    # -----------------------------------------
    # CPU Usage
    # -----------------------------------------

    def cpu_usage(self):

        latest = (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).first()
        )

        if latest is None:
            return 0

        return latest.cpu_usage

    # -----------------------------------------
    # Memory Usage
    # -----------------------------------------

    def memory_usage(self):

        latest = (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).first()
        )

        if latest is None:
            return 0

        return latest.memory_usage

    # -----------------------------------------
    # Disk Usage
    # -----------------------------------------

    def disk_usage(self):

        latest = (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).first()
        )

        if latest is None:
            return 0

        return latest.disk_usage

    # -----------------------------------------
    # Network Usage
    # -----------------------------------------

    def network_usage(self):

        latest = (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).first()
        )

        if latest is None:
            return 0

        return latest.network_usage

    # -----------------------------------------
    # Detection Labels
    # -----------------------------------------

    def detection_labels(self):

        rows = (
            self.db.query(
                Detection.label,
                func.count(
                    Detection.id,
                ),
            )
            .group_by(
                Detection.label,
            )
            .order_by(
                func.count(
                    Detection.id,
                ).desc()
            )
            .all()
        )

        return [
            {
                "label": row[0],
                "count": row[1],
            }
            for row in rows
        ]

    # -----------------------------------------
    # Dashboard
    # -----------------------------------------

    def get_dashboard_data(self):

        return {
            "ai_status": self.ai_status(),
            "total_detections": self.total_detections(),
            "average_confidence": self.average_confidence(),
            "highest_confidence": self.highest_confidence(),
            "lowest_confidence": self.lowest_confidence(),
            "cpu_usage": self.cpu_usage(),
            "memory_usage": self.memory_usage(),
            "disk_usage": self.disk_usage(),
            "network_usage": self.network_usage(),
            "detection_labels": self.detection_labels(),
        }
