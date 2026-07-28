from sqlalchemy.orm import Session

from src.models.camera import Camera


class CameraRepository:
    """
    Repository responsible for Camera database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, camera: Camera) -> Camera:
        self.db.add(camera)
        self.db.commit()
        self.db.refresh(camera)
        return camera

    def get_by_id(self, camera_id: int) -> Camera | None:
        return self.db.query(Camera).filter(Camera.id == camera_id).first()

    def get_by_rtsp_url(self, rtsp_url: str) -> Camera | None:
        return self.db.query(Camera).filter(Camera.rtsp_url == rtsp_url).first()

    def get_all(self):
        return self.db.query(Camera).order_by(Camera.id).all()

    def update(self, camera: Camera) -> Camera:
        self.db.commit()
        self.db.refresh(camera)
        return camera

    def delete(self, camera: Camera):
        self.db.delete(camera)
        self.db.commit()
