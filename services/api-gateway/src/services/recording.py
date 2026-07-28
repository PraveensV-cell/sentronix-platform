import os

from sqlalchemy.orm import Session

from src.models.recording import Recording
from src.repositories.recording_repository import RecordingRepository
from src.schemas.recording import RecordingCreate


class RecordingService:
    """
    Business logic for recording management.
    """

    def __init__(self, db: Session):
        self.repository = RecordingRepository(db)

    def create_recording(
        self,
        recording_data: RecordingCreate,
    ) -> Recording:

        recording = Recording(
            camera_id=recording_data.camera_id,
            file_name=recording_data.file_name,
            file_path=recording_data.file_path,
            duration=recording_data.duration,
            size=recording_data.size,
            start_time=recording_data.start_time,
            end_time=recording_data.end_time,
        )

        return self.repository.create(recording)

    def list_recordings(self):

        return self.repository.get_all()

    def get_recording(
        self,
        recording_id: int,
    ):

        return self.repository.get_by_id(recording_id)

    def get_camera_recordings(
        self,
        camera_id: int,
    ):

        return self.repository.get_by_camera(camera_id)

    def delete_recording(
        self,
        recording_id: int,
    ):

        recording = self.repository.get_by_id(recording_id)

        if recording is None:
            return False

        if os.path.exists(recording.file_path):
            os.remove(recording.file_path)

        self.repository.delete(recording)

        return True
