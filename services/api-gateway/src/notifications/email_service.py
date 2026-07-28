import aiosmtplib

from email.message import EmailMessage

from src.core.config import settings


class EmailService:
    """
    Sends alert emails.
    """

    async def send_alert(
        self,
        subject: str,
        body: str,
        recipient: str,
    ):

        message = EmailMessage()

        message["From"] = settings.SMTP_FROM

        message["To"] = recipient

        message["Subject"] = subject

        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
