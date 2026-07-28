from src.core.logger import logger
from src.schemas.notification import NotificationResponse


class WebhookService:
    def send(
        self,
        notification: NotificationResponse,
    ) -> None:

        logger.info(f"Webhook Notification : {notification.notification_id}")

        logger.success("Webhook Delivered.")
