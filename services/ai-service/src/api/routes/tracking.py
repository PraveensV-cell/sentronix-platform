from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException

from src.services.tracking_service import (
    tracking_service,
)


router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"],
)


@router.get("/")
def all_tracking():
    """
    Get all tracked objects.
    """

    return {
        "success": True,
        "objects": tracking_service.get_all(),
    }


@router.get("/stats")
def tracking_stats():
    """
    Get tracking statistics.
    """

    return {
        "success": True,
        "statistics": tracking_service.statistics(),
    }


@router.get("/{object_id}")
def object_history(
    object_id: str,
):
    """
    Get object tracking history.
    """

    history = tracking_service.get_history(
        object_id,
    )

    if not history:
        raise HTTPException(
            status_code=404,
            detail="Object history not found.",
        )

    return {
        "success": True,
        "object_id": object_id,
        "history": history,
    }


@router.delete("/{object_id}")
def remove_object(
    object_id: str,
):
    """
    Remove object tracking history.
    """

    removed = tracking_service.remove(
        object_id,
    )

    if removed is None:
        raise HTTPException(
            status_code=404,
            detail="Object not found.",
        )

    return {
        "success": True,
        "message": "Tracking history removed.",
    }


@router.delete("/")
def clear_tracking():
    """
    Clear all tracking history.
    """

    tracking_service.clear()

    return {
        "success": True,
        "message": "All tracking history cleared.",
    }
