import uuid
from datetime import datetime
from typing import Any

from src.core.logger import logger
from src.schemas.notification import DetectionNotificationRequest
from src.schemas.notification import NotificationCreate
from src.schemas.notification import NotificationResponse
from src.services.email_service import EmailService
from src.services.webhook_service import WebhookService


class NotificationService:
    def __init__(self):

        self.notifications: list[NotificationResponse] = []

        self.detection_notifications: list[dict[str, Any]] = []

        self.email_service = EmailService()

        self.webhook_service = WebhookService()

    def send(
        self,
        request: NotificationCreate,
    ) -> NotificationResponse:

        notification = NotificationResponse(
            notification_id=str(uuid.uuid4()),
            recipient=request.recipient,
            subject=request.subject,
            message=request.message,
            channel=request.channel,
            status="sent",
            created_at=datetime.utcnow(),
        )

        if request.channel.lower() == "email":
            self.email_service.send_email(notification)

        elif request.channel.lower() == "webhook":
            self.webhook_service.send(notification)

        self.notifications.append(notification)

        logger.info(f"Notification Sent : {notification.notification_id}")

        return notification

    def get_all(
        self,
    ) -> list[NotificationResponse]:

        return self.notifications

    def get(
        self,
        notification_id: str,
    ):

        for notification in self.notifications:
            if notification.notification_id == notification_id:
                return notification

        return None

    def delete(
        self,
        notification_id: str,
    ) -> bool:

        for notification in self.notifications:
            if notification.notification_id == notification_id:
                self.notifications.remove(notification)

                return True

        return False

    # ==========================================================
    # Detection Event Notifications
    # ==========================================================

    def receive_detection_event(
        self,
        event: DetectionNotificationRequest,
    ):

        self.detection_notifications.append(event.model_dump())

        notification = NotificationCreate(
            recipient="admin@sentronix.com",
            subject="AI Detection Alert",
            message=f"Camera {event.camera_id} detected {len(event.detections)} object(s).",
            channel="email",
        )

        self.send(notification)

        logger.info(f"Detection Notification Created : {event.event_id}")

        return {
            "message": "Detection notification processed.",
            "total_notifications": len(self.detection_notifications),
        }

    def get_detection_notifications(
        self,
    ):

        return self.detection_notifications


notification_service = NotificationService()
