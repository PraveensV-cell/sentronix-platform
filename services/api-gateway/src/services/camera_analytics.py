from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.alert import Alert
from src.models.camera import Camera
from src.models.detection import Detection
from src.models.recording import Recording


class CameraAnalyticsService:
    """
    Camera Analytics Service.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # -----------------------------------------
    # Total Cameras
    # -----------------------------------------

    def total_cameras(self):

        return self.db.query(Camera).count()

    # -----------------------------------------
    # Online Cameras
    # -----------------------------------------

    def online_cameras(self):

        return self.db.query(Camera).filter(Camera.status == "online").count()

    # -----------------------------------------
    # Offline Cameras
    # -----------------------------------------

    def offline_cameras(self):

        return self.db.query(Camera).filter(Camera.status == "offline").count()

    # -----------------------------------------
    # Active Cameras
    # -----------------------------------------

    def active_cameras(self):

        return self.db.query(Camera).filter(Camera.is_active.is_(True)).count()

    # -----------------------------------------
    # Camera Detection Statistics
    # -----------------------------------------

    def detections_per_camera(self):

        rows = (
            self.db.query(
                Detection.camera_id,
                func.count(
                    Detection.id,
                ),
            )
            .group_by(
                Detection.camera_id,
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
    # Camera Alert Statistics
    # -----------------------------------------

    def alerts_per_camera(self):

        rows = (
            self.db.query(
                Alert.camera_id,
                func.count(
                    Alert.id,
                ),
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
    # Camera Recording Statistics
    # -----------------------------------------

    def recordings_per_camera(self):

        rows = (
            self.db.query(
                Recording.camera_id,
                func.count(
                    Recording.id,
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
            }
            for row in rows
        ]

    # -----------------------------------------
    # Camera Utilization
    # -----------------------------------------

    def camera_utilization(self):

        total = self.total_cameras()

        online = self.online_cameras()

        utilization = 0.0

        if total > 0:
            utilization = round(
                (online / total) * 100,
                2,
            )

        return {
            "online": online,
            "offline": self.offline_cameras(),
            "utilization_percent": utilization,
        }

    # -----------------------------------------
    # Dashboard Data
    # -----------------------------------------

    def get_dashboard_data(self):

        return {
            "total_cameras": self.total_cameras(),
            "online_cameras": self.online_cameras(),
            "offline_cameras": self.offline_cameras(),
            "active_cameras": self.active_cameras(),
            "camera_utilization": self.camera_utilization(),
            "detections_per_camera": self.detections_per_camera(),
            "alerts_per_camera": self.alerts_per_camera(),
            "recordings_per_camera": self.recordings_per_camera(),
        }
