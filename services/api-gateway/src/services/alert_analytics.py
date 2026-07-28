from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.alert import Alert


class AlertAnalyticsService:
    """
    Alert Analytics Service.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # -----------------------------------------
    # Total Alerts
    # -----------------------------------------

    def total_alerts(self):

        return self.db.query(Alert).count()

    # -----------------------------------------
    # Alerts by Severity
    # -----------------------------------------

    def alerts_by_severity(self):

        rows = (
            self.db.query(
                Alert.severity,
                func.count(Alert.id),
            )
            .group_by(
                Alert.severity,
            )
            .all()
        )

        return [
            {
                "severity": row[0],
                "count": row[1],
            }
            for row in rows
        ]

    # -----------------------------------------
    # Alerts by Status
    # -----------------------------------------

    def alerts_by_status(self):

        rows = (
            self.db.query(
                Alert.status,
                func.count(Alert.id),
            )
            .group_by(
                Alert.status,
            )
            .all()
        )

        return [
            {
                "status": row[0],
                "count": row[1],
            }
            for row in rows
        ]

    # -----------------------------------------
    # Alerts by Camera
    # -----------------------------------------

    def alerts_by_camera(self):

        rows = (
            self.db.query(
                Alert.camera_id,
                func.count(Alert.id),
            )
            .group_by(
                Alert.camera_id,
            )
            .all()
        )

        return [
            {
                "camera_id": row[0],
                "alerts": row[1],
            }
            for row in rows
        ]

    # -----------------------------------------
    # Daily Trend
    # -----------------------------------------

    def daily_trend(self):

        rows = (
            self.db.query(
                func.date(Alert.created_at),
                func.count(Alert.id),
            )
            .group_by(
                func.date(Alert.created_at),
            )
            .order_by(
                func.date(Alert.created_at),
            )
            .all()
        )

        return {
            "labels": [str(row[0]) for row in rows],
            "values": [row[1] for row in rows],
        }

    # -----------------------------------------
    # Alert Titles
    # -----------------------------------------

    def alert_titles(self):

        rows = (
            self.db.query(
                Alert.title,
                func.count(Alert.id),
            )
            .group_by(
                Alert.title,
            )
            .order_by(
                func.count(Alert.id).desc(),
            )
            .all()
        )

        return [
            {
                "title": row[0],
                "count": row[1],
            }
            for row in rows
        ]

    # -----------------------------------------
    # Date Range
    # -----------------------------------------

    def date_range(
        self,
        start: datetime,
        end: datetime,
    ):

        return (
            self.db.query(Alert)
            .filter(
                Alert.created_at >= start,
                Alert.created_at <= end,
            )
            .all()
        )

    # -----------------------------------------
    # Dashboard Data
    # -----------------------------------------

    def get_dashboard_data(self):

        return {
            "total_alerts": self.total_alerts(),
            "alerts_by_severity": self.alerts_by_severity(),
            "alerts_by_status": self.alerts_by_status(),
            "alerts_by_camera": self.alerts_by_camera(),
            "alert_titles": self.alert_titles(),
            "daily_trend": self.daily_trend(),
        }
