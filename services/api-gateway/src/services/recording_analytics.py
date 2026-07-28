from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.recording import Recording


class RecordingAnalyticsService:
    """
    Recording Analytics Service.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # -----------------------------------------
    # Total Recordings
    # -----------------------------------------

    def total_recordings(self):

        return self.db.query(Recording).count()

    # -----------------------------------------
    # Total Storage Used (MB)
    # -----------------------------------------

    def total_storage(self):

        total = self.db.query(
            func.sum(
                Recording.size,
            )
        ).scalar()

        return round(
            float(total or 0),
            2,
        )

    # -----------------------------------------
    # Total Duration (Seconds)
    # -----------------------------------------

    def total_duration(self):

        duration = self.db.query(
            func.sum(
                Recording.duration,
            )
        ).scalar()

        return round(
            float(duration or 0),
            2,
        )

    # -----------------------------------------
    # Average Recording Duration
    # -----------------------------------------

    def average_duration(self):

        avg = self.db.query(
            func.avg(
                Recording.duration,
            )
        ).scalar()

        return round(
            float(avg or 0),
            2,
        )

    # -----------------------------------------
    # Camera Statistics
    # -----------------------------------------

    def recordings_by_camera(self):

        rows = (
            self.db.query(
                Recording.camera_id,
                func.count(
                    Recording.id,
                ),
                func.sum(
                    Recording.size,
                ),
            )
            .group_by(
                Recording.camera_id,
            )
            .all()
        )

        return [
            {
                "camera_id": row[0],
                "recordings": row[1],
                "storage_mb": round(
                    float(row[2] or 0),
                    2,
                ),
            }
            for row in rows
        ]

    # -----------------------------------------
    # Daily Trend
    # -----------------------------------------

    def daily_trend(self):

        rows = (
            self.db.query(
                func.date(
                    Recording.created_at,
                ),
                func.count(
                    Recording.id,
                ),
            )
            .group_by(
                func.date(
                    Recording.created_at,
                )
            )
            .order_by(
                func.date(
                    Recording.created_at,
                )
            )
            .all()
        )

        return {
            "labels": [str(row[0]) for row in rows],
            "values": [row[1] for row in rows],
        }

    # -----------------------------------------
    # Storage Growth
    # -----------------------------------------

    def storage_growth(self):

        rows = (
            self.db.query(
                func.date(
                    Recording.created_at,
                ),
                func.sum(
                    Recording.size,
                ),
            )
            .group_by(
                func.date(
                    Recording.created_at,
                )
            )
            .order_by(
                func.date(
                    Recording.created_at,
                )
            )
            .all()
        )

        return {
            "labels": [str(row[0]) for row in rows],
            "values": [
                round(
                    float(row[1] or 0),
                    2,
                )
                for row in rows
            ],
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
            self.db.query(Recording)
            .filter(
                Recording.created_at >= start,
                Recording.created_at <= end,
            )
            .all()
        )

    # -----------------------------------------
    # Dashboard Data
    # -----------------------------------------

    def get_dashboard_data(self):

        return {
            "total_recordings": self.total_recordings(),
            "total_storage_mb": self.total_storage(),
            "total_duration_seconds": self.total_duration(),
            "average_duration_seconds": self.average_duration(),
            "recordings_by_camera": self.recordings_by_camera(),
            "daily_trend": self.daily_trend(),
            "storage_growth": self.storage_growth(),
        }
