from src.core.logger import logger
from src.schemas.notification import NotificationResponse


class EmailService:
    def send_email(
        self,
        notification: NotificationResponse,
    ) -> None:

        logger.info(f"Sending Email To : {notification.recipient}")

        logger.info(f"Subject : {notification.subject}")

        logger.success("Email Sent Successfully.")
