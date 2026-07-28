from fastapi import APIRouter

from src.schemas.analytics import AnalyticsEventRequest
from src.schemas.analytics import AnalyticsResponse
from src.services.analytics_service import AnalyticsService

router = APIRouter()

analytics_service = AnalyticsService()


@router.get(
    "/summary",
    response_model=AnalyticsResponse,
)
async def summary():

    return analytics_service.summary()


@router.get("/metrics")
async def metrics():

    return analytics_service.metrics()


@router.get("/report")
async def report():

    return analytics_service.report()


# ==========================================================
# Detection Events
# ==========================================================


@router.post("/events")
async def receive_event(
    event: AnalyticsEventRequest,
):

    return analytics_service.add_event(
        event.model_dump(),
    )


@router.get("/events")
async def get_events():

    return analytics_service.get_events()
