from sqlalchemy.orm import Session

from src.models.detection import Detection
from src.repositories.detection_repository import DetectionRepository
from src.schemas.detection import (
    DetectionCreate,
    DetectionUpdate,
)


class DetectionService:
    """
    Business logic for AI detections.
    """

    def __init__(self, db: Session):
        self.repository = DetectionRepository(db)

    def create_detection(
        self,
        detection_data: DetectionCreate,
    ) -> Detection:
        """
        Save a new AI detection.
        """

        detection = Detection(
            camera_id=detection_data.camera_id,
            label=detection_data.label,
            confidence=detection_data.confidence,
            x1=detection_data.x1,
            y1=detection_data.y1,
            x2=detection_data.x2,
            y2=detection_data.y2,
        )

        return self.repository.create(detection)

    def get_detection(
        self,
        detection_id: int,
    ) -> Detection | None:
        """
        Get one detection.
        """

        return self.repository.get_by_id(detection_id)

    def list_detections(self) -> list[Detection]:
        """
        Return all detections.
        """

        return self.repository.get_all()

    def list_camera_detections(
        self,
        camera_id: int,
    ) -> list[Detection]:
        """
        Return detections for one camera.
        """

        return self.repository.get_by_camera(camera_id)

    def list_label_detections(
        self,
        label: str,
    ) -> list[Detection]:
        """
        Return detections having the given label.
        """

        return self.repository.get_by_label(label)

    def update_detection(
        self,
        detection_id: int,
        detection_data: DetectionUpdate,
    ) -> Detection | None:
        """
        Update detection information.
        """

        detection = self.repository.get_by_id(detection_id)

        if detection is None:
            return None

        update_data = detection_data.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(
                detection,
                field,
                value,
            )

        return self.repository.update(detection)

    def delete_detection(
        self,
        detection_id: int,
    ) -> bool:
        """
        Delete a detection.
        """

        detection = self.repository.get_by_id(
            detection_id,
        )

        if detection is None:
            return False

        self.repository.delete(detection)

        return True

    def delete_camera_detections(
        self,
        camera_id: int,
    ) -> int:
        """
        Delete all detections belonging to one camera.
        """

        return self.repository.delete_all_by_camera(
            camera_id,
        )

    def total_detections(self) -> int:
        """
        Return total number of detections.
        """

        return self.repository.count()
