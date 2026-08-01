from fastapi import APIRouter

from src.services.health_service import (
    health_service,
)


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
def health():
    """
    Basic health endpoint.
    """

    return health_service.get_health()


@router.get("/details")
def health_details():
    """
    Detailed AI service health information.
    """

    return health_service.get_details()
