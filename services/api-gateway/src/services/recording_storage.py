from sqlalchemy.orm import Session

from src.models.recording import Recording


class RecordingStorage:
    """
    Stores recording metadata in the database.
    """

    def __init__(self, db: Session):
        self.db = db

    def save(
        self,
        camera_id: int,
        metadata: dict,
    ) -> Recording:
        """
        Save recording metadata.
        """

        recording = Recording(
            camera_id=camera_id,
            file_name=metadata["file_name"],
            file_path=metadata["file_path"],
            duration=metadata["duration"],
            size=metadata["size"],
            start_time=metadata["start_time"],
            end_time=metadata["end_time"],
        )

        self.db.add(recording)
        self.db.commit()
        self.db.refresh(recording)

        return recording
