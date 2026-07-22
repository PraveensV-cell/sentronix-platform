from fastapi import APIRouter
from src.core.health import health_status
from src.core.service_registry import registry
from src.core.service import get_service_information

router = APIRouter(tags=["System"])


@router.get("/")
async def root():
    return {
        "application": "SENTRONIX",
        "service": "API Gateway",
        "status": "Running",
    }


@router.get("/health")
async def health():
    return health_status()


@router.get("/services")
async def services():
    return registry.get_all()


@router.get("/service")
async def service():

    return get_service_information()
