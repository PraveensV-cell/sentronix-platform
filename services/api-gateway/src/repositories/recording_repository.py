from sqlalchemy.orm import Session

from src.models.recording import Recording


class RecordingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        recording: Recording,
    ):
        self.db.add(recording)
        self.db.commit()
        self.db.refresh(recording)
        return recording

    def get_all(self):
        return self.db.query(Recording).order_by(Recording.created_at.desc()).all()

    def get_by_camera(
        self,
        camera_id: int,
    ):
        return (
            self.db.query(Recording)
            .filter(Recording.camera_id == camera_id)
            .order_by(Recording.created_at.desc())
            .all()
        )

    def get_by_id(
        self,
        recording_id: int,
    ):
        return self.db.query(Recording).filter(Recording.id == recording_id).first()

    def delete(
        self,
        recording: Recording,
    ):
        self.db.delete(recording)
        self.db.commit()
