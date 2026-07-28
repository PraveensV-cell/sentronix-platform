from sqlalchemy.orm import Session

from src.models.detection import Detection


class DetectionRepository:
    """
    Repository for Detection database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        detection: Detection,
    ) -> Detection:
        """
        Create a new detection.
        """

        self.db.add(detection)
        self.db.commit()
        self.db.refresh(detection)

        return detection

    def get_by_id(
        self,
        detection_id: int,
    ) -> Detection | None:
        """
        Get detection by ID.
        """

        return self.db.query(Detection).filter(Detection.id == detection_id).first()

    def get_all(self) -> list[Detection]:
        """
        Return all detections.
        """

        return self.db.query(Detection).order_by(Detection.detected_at.desc()).all()

    def get_by_camera(
        self,
        camera_id: int,
    ) -> list[Detection]:
        """
        Return detections for one camera.
        """

        return (
            self.db.query(Detection)
            .filter(Detection.camera_id == camera_id)
            .order_by(Detection.detected_at.desc())
            .all()
        )

    def get_by_label(
        self,
        label: str,
    ) -> list[Detection]:
        """
        Return detections by object label.
        """

        return (
            self.db.query(Detection)
            .filter(Detection.label == label)
            .order_by(Detection.detected_at.desc())
            .all()
        )

    def update(
        self,
        detection: Detection,
    ) -> Detection:
        """
        Update detection.
        """

        self.db.commit()
        self.db.refresh(detection)

        return detection

    def delete(
        self,
        detection: Detection,
    ) -> None:
        """
        Delete detection.
        """

        self.db.delete(detection)
        self.db.commit()

    def delete_all_by_camera(
        self,
        camera_id: int,
    ) -> int:
        """
        Delete all detections for a camera.
        """

        deleted = (
            self.db.query(Detection).filter(Detection.camera_id == camera_id).delete()
        )

        self.db.commit()

        return deleted

    def count(self) -> int:
        """
        Return total detections.
        """

        return self.db.query(Detection).count()
