from sqlalchemy.orm import Session

from src.models.alert import Alert
from src.repositories.alert_repository import AlertRepository
from src.schemas.alert import (
    AlertCreate,
    AlertUpdate,
)


class AlertService:
    """
    Business logic for alerts.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.repository = AlertRepository(db)

    def create_alert(
        self,
        alert_data: AlertCreate,
    ) -> Alert:

        alert = Alert(
            camera_id=alert_data.camera_id,
            detection_id=alert_data.detection_id,
            title=alert_data.title,
            message=alert_data.message,
            severity=alert_data.severity,
            status=alert_data.status,
        )

        return self.repository.create(alert)

    def get_alert(
        self,
        alert_id: int,
    ):

        return self.repository.get_by_id(alert_id)

    def list_alerts(self):

        return self.repository.get_all()

    def update_alert(
        self,
        alert_id: int,
        alert_data: AlertUpdate,
    ):

        alert = self.repository.get_by_id(alert_id)

        if alert is None:
            return None

        update_data = alert_data.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(
                alert,
                field,
                value,
            )

        return self.repository.update(alert)

    def delete_alert(
        self,
        alert_id: int,
    ):

        alert = self.repository.get_by_id(alert_id)

        if alert is None:
            return False

        self.repository.delete(alert)

        return True

    def total_alerts(self):

        return self.repository.count()
