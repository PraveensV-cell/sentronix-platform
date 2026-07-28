from fastapi import APIRouter

from src.services.health_service import HealthService

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
def health():
    """
    Health endpoint.
    """

    return HealthService().get_health()
