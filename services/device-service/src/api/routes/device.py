from fastapi import APIRouter
from fastapi import HTTPException

from src.schemas.device import DeviceInfo
from src.schemas.device import DeviceRegistration
from src.schemas.device import DeviceStatus
from src.services.device_service import DeviceService

router = APIRouter()

device_service = DeviceService()


@router.post(
    "/register",
    response_model=DeviceInfo,
)
async def register_device(
    device: DeviceRegistration,
):
    """
    Register a new device.
    """

    return device_service.register_device(device)


@router.get(
    "/info",
    response_model=DeviceInfo,
)
async def get_device_info():
    """
    Get current device information.
    """

    return device_service.get_device_info()


@router.get(
    "/status",
    response_model=DeviceStatus,
)
async def get_device_status():
    """
    Get device status.
    """

    return device_service.get_device_status()


@router.post("/heartbeat")
async def heartbeat():
    """
    Send heartbeat.
    """

    success = device_service.send_heartbeat()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Heartbeat failed",
        )

    return {
        "message": "Heartbeat sent successfully",
    }
