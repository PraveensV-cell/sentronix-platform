from sqlalchemy.orm import Session

from src.models.alert import Alert


class AlertRepository:
    """
    Repository for Alert operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        alert: Alert,
    ) -> Alert:

        self.db.add(alert)

        self.db.commit()

        self.db.refresh(alert)

        return alert

    def get_by_id(
        self,
        alert_id: int,
    ) -> Alert | None:

        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def get_all(self):

        return self.db.query(Alert).order_by(Alert.created_at.desc()).all()

    def update(
        self,
        alert: Alert,
    ) -> Alert:

        self.db.commit()

        self.db.refresh(alert)

        return alert

    def delete(
        self,
        alert: Alert,
    ):

        self.db.delete(alert)

        self.db.commit()

    def count(self):

        return self.db.query(Alert).count()
