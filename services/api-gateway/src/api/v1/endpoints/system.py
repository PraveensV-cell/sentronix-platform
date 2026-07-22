from fastapi import APIRouter
from src.core.health import health_status

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
