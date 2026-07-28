from sqlalchemy.orm import Session

from src.models.camera import Camera
from src.repositories.camera_repository import CameraRepository
from src.schemas.camera import CameraCreate, CameraUpdate
from src.utils.camera import (
    check_camera_connection,
    is_valid_rtsp_url,
)


class CameraService:
    """
    Business logic for camera management.
    """

    def __init__(self, db: Session):
        self.repository = CameraRepository(db)

    def create_camera(
        self,
        camera_data: CameraCreate,
    ) -> Camera:
        """
        Register a new camera.
        """

        # Validate RTSP URL format
        if not is_valid_rtsp_url(camera_data.rtsp_url):
            raise ValueError("Invalid RTSP URL.")

        # Check duplicate RTSP URL
        existing_camera = self.repository.get_by_rtsp_url(camera_data.rtsp_url)

        if existing_camera:
            raise ValueError("Camera with this RTSP URL already exists.")

        # Check camera connectivity
        status = (
            "online" if check_camera_connection(camera_data.rtsp_url) else "offline"
        )

        camera = Camera(
            name=camera_data.name,
            location=camera_data.location,
            rtsp_url=camera_data.rtsp_url,
            camera_type=camera_data.camera_type,
            zone=camera_data.zone,
            status=status,
            is_active=True,
        )

        return self.repository.create(camera)

    def get_camera(
        self,
        camera_id: int,
    ) -> Camera | None:
        """
        Get a camera by ID.
        """

        return self.repository.get_by_id(camera_id)

    def list_cameras(self):
        """
        Return all registered cameras.
        """

        return self.repository.get_all()

    def update_camera(
        self,
        camera_id: int,
        camera_data: CameraUpdate,
    ) -> Camera | None:
        """
        Update camera information.
        """

        camera = self.repository.get_by_id(camera_id)

        if camera is None:
            return None

        update_data = camera_data.model_dump(exclude_unset=True)

        # Validate RTSP URL if updated
        if "rtsp_url" in update_data:
            if not is_valid_rtsp_url(update_data["rtsp_url"]):
                raise ValueError("Invalid RTSP URL.")

            existing = self.repository.get_by_rtsp_url(update_data["rtsp_url"])

            if existing and existing.id != camera.id:
                raise ValueError("Camera with this RTSP URL already exists.")

        for field, value in update_data.items():
            setattr(camera, field, value)

        return self.repository.update(camera)

    def delete_camera(
        self,
        camera_id: int,
    ) -> bool:
        """
        Delete a camera.
        """

        camera = self.repository.get_by_id(camera_id)

        if camera is None:
            return False

        self.repository.delete(camera)

        return True

    def refresh_camera_status(
        self,
        camera_id: int,
    ) -> Camera | None:
        """
        Refresh the online/offline status of a camera.
        """

        camera = self.repository.get_by_id(camera_id)

        if camera is None:
            return None

        camera.status = (
            "online" if check_camera_connection(camera.rtsp_url) else "offline"
        )

        return self.repository.update(camera)
