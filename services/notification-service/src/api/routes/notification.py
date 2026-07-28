from fastapi import APIRouter, HTTPException

from src.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    EventNotificationRequest,
    DetectionNotificationRequest,
)
from src.services.notification_service import NotificationService

router = APIRouter()

notification_service = NotificationService()


@router.post(
    "/",
    response_model=NotificationResponse,
)
async def send_notification(
    notification: NotificationCreate,
):
    """
    Send a notification.
    """
    return notification_service.send(notification)


@router.get(
    "/",
    response_model=list[NotificationResponse],
)
async def get_notifications():
    """
    Return all notifications.
    """
    return notification_service.get_all()


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: str,
):
    """
    Return a notification.
    """

    notification = notification_service.get(notification_id)

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return notification


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
):
    """
    Delete notification.
    """

    success = notification_service.delete(notification_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return {
        "message": "Notification deleted successfully",
    }


# ==========================================================
# Event Notifications
# ==========================================================


@router.post("/events")
async def receive_event(
    event: EventNotificationRequest,
):
    """
    Receive events from Event Service.
    """

    return notification_service.process_event(event)


# ==========================================================
# Detection Notifications
# ==========================================================


@router.post("/detection")
async def receive_detection_notification(
    event: DetectionNotificationRequest,
):
    """
    Receive forwarded AI detection events.
    """

    return notification_service.receive_detection_event(
        event,
    )


@router.get("/detection")
async def get_detection_notifications():
    """
    Return received detection notifications.
    """

    return notification_service.get_detection_notifications()
