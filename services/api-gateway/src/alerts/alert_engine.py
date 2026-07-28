import asyncio

from sqlalchemy.orm import Session

from src.alerts.rules import ALERT_RULES
from src.core.config import settings
from src.notifications.email_service import EmailService
from src.recording import recording_manager
from src.schemas.alert import AlertCreate
from src.services.alert import AlertService
from src.streaming.manager import stream_manager
from src.websocket import manager


class AlertEngine:
    def __init__(self, db: Session):
        self.service = AlertService(db)

    def process_detection(self, detection):

        rule = ALERT_RULES.get(detection.label.lower())

        if rule is None:
            return None

        if not rule["enabled"]:
            return None

        alert = self.service.create_alert(
            AlertCreate(
                camera_id=detection.camera_id,
                detection_id=detection.id,
                title=f"{detection.label} Detected",
                message=(
                    f"{detection.label} detected "
                    f"with confidence "
                    f"{detection.confidence:.2f}"
                ),
                severity=rule["severity"],
                status="OPEN",
            )
        )

        if rule["severity"] == "CRITICAL":
            stream = stream_manager.streams.get(detection.camera_id)

            if stream is not None:
                frame = stream.get_raw_frame()

                if frame is not None:
                    recording_manager.start_recording(
                        detection.camera_id,
                        frame,
                    )

        payload = {
            "id": alert.id,
            "camera_id": detection.camera_id,
            "detection_id": detection.id,
            "label": detection.label,
            "confidence": detection.confidence,
            "severity": rule["severity"],
            "title": alert.title,
            "message": alert.message,
            "status": alert.status,
        }

        try:
            loop = asyncio.get_running_loop()

            loop.create_task(manager.broadcast(payload))

            if rule["severity"] == "CRITICAL":
                loop.create_task(
                    EmailService().send_alert(
                        subject=f"SENTRONIX ALERT - {detection.label}",
                        body=f"""
SENTRONIX Critical Alert

Camera ID : {detection.camera_id}

Detection ID : {detection.id}

Object : {detection.label}

Confidence : {detection.confidence:.2f}

Severity : {rule["severity"]}

Please check the camera immediately.
""",
                        recipient=settings.ADMIN_EMAIL,
                    )
                )

        except RuntimeError:
            print(
                "[AlertEngine] No running asyncio event loop. "
                "Skipping WebSocket and Email notification."
            )

        return alert
