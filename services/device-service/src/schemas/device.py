from datetime import datetime

from pydantic import BaseModel


class DeviceRegistration(BaseModel):
    """
    Device registration request.
    """

    device_name: str
    location: str
    ip_address: str


class DeviceInfo(BaseModel):
    """
    Device information response.
    """

    device_id: str
    device_name: str
    location: str
    ip_address: str
    status: str
    registered_at: datetime


class DeviceStatus(BaseModel):
    """
    Device status response.
    """

    device_id: str
    status: str
    last_heartbeat: datetime
