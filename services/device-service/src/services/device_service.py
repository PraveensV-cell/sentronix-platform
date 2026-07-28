from datetime import datetime

from src.core.config import settings
from src.core.logger import logger
from src.schemas.device import DeviceInfo
from src.schemas.device import DeviceRegistration
from src.schemas.device import DeviceStatus


class DeviceService:
    """
    Device Service Business Logic
    """

    def __init__(self):
        self.device = DeviceInfo(
            device_id=settings.DEVICE_ID,
            device_name="Sentronix Camera Device",
            location="Unknown",
            ip_address="127.0.0.1",
            status="online",
            registered_at=datetime.utcnow(),
        )

        self.last_heartbeat = datetime.utcnow()

    def register_device(
        self,
        request: DeviceRegistration,
    ) -> DeviceInfo:
        """
        Register a device.
        """

        self.device.device_name = request.device_name
        self.device.location = request.location
        self.device.ip_address = request.ip_address
        self.device.registered_at = datetime.utcnow()

        logger.info(f"Device Registered : {request.device_name}")

        return self.device

    def get_device_info(
        self,
    ) -> DeviceInfo:
        """
        Return current device information.
        """

        return self.device

    def get_device_status(
        self,
    ) -> DeviceStatus:
        """
        Return device status.
        """

        return DeviceStatus(
            device_id=self.device.device_id,
            status=self.device.status,
            last_heartbeat=self.last_heartbeat,
        )

    def send_heartbeat(
        self,
    ) -> bool:
        """
        Update heartbeat timestamp.
        """

        self.last_heartbeat = datetime.utcnow()

        logger.info("Heartbeat sent.")

        return True
