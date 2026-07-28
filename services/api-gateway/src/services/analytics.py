from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.camera import Camera
from src.models.detection import Detection


class AnalyticsService:
    """
    Analytics Service.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # -----------------------------------------
    # Total Detections
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
    # Detection Count by Label
    # -----------------------------------------

    def detections_by_label(self):

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
                ).desc(),
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
    # Camera Statistics
    # -----------------------------------------

    def camera_statistics(self):

        rows = (
            self.db.query(
                Camera.id,
                func.count(
                    Detection.id,
                ),
            )
            .outerjoin(
                Detection,
                Camera.id == Detection.camera_id,
            )
            .group_by(
                Camera.id,
            )
            .all()
        )

        return [
            {
                "camera_id": row[0],
                "detections": row[1],
            }
            for row in rows
        ]

    # -----------------------------------------
    # Hourly Trend
    # -----------------------------------------

    def hourly_trend(self):

        rows = (
            self.db.query(
                func.strftime(
                    "%H",
                    Detection.detected_at,
                ),
                func.count(
                    Detection.id,
                ),
            )
            .group_by(
                func.strftime(
                    "%H",
                    Detection.detected_at,
                ),
            )
            .order_by(
                func.strftime(
                    "%H",
                    Detection.detected_at,
                ),
            )
            .all()
        )

        return {
            "labels": [row[0] for row in rows],
            "values": [row[1] for row in rows],
        }

    # -----------------------------------------
    # Daily Trend
    # -----------------------------------------

    def daily_trend(self):

        rows = (
            self.db.query(
                func.date(
                    Detection.detected_at,
                ),
                func.count(
                    Detection.id,
                ),
            )
            .group_by(
                func.date(
                    Detection.detected_at,
                ),
            )
            .order_by(
                func.date(
                    Detection.detected_at,
                ),
            )
            .all()
        )

        return {
            "labels": [str(row[0]) for row in rows],
            "values": [row[1] for row in rows],
        }

    # -----------------------------------------
    # Date Range
    # -----------------------------------------

    def date_range(
        self,
        start: datetime,
        end: datetime,
    ):

        return (
            self.db.query(
                Detection,
            )
            .filter(
                Detection.detected_at >= start,
                Detection.detected_at <= end,
            )
            .all()
        )

    # -----------------------------------------
    # Dashboard Data
    # -----------------------------------------

    def get_dashboard_data(self):

        return {
            "total_detections": self.total_detections(),
            "average_confidence": self.average_confidence(),
            "detections_by_label": self.detections_by_label(),
            "camera_statistics": self.camera_statistics(),
            "hourly_trend": self.hourly_trend(),
            "daily_trend": self.daily_trend(),
        }
