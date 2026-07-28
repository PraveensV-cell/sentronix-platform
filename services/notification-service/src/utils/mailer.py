from src.core.logger import logger


class Mailer:
    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
    ) -> bool:
        """
        Placeholder mail sender.
        Replace with SMTP implementation later.
        """

        logger.info(f"Sending email to {recipient}")

        logger.info(f"Subject: {subject}")

        logger.info(f"Message: {message}")

        logger.success("Email sent successfully.")

        return True
