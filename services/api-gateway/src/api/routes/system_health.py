from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.health import services_health
from src.database.session import get_db
from src.monitor.ai_monitor import AIMonitor
from src.monitor.camera_monitor import CameraMonitor
from src.monitor.database_monitor import DatabaseMonitor
from src.monitor.system_monitor import SystemMonitor
from src.services.service_health import service_health
from src.services.system_health import SystemHealthService

router = APIRouter(
    prefix="/health",
    tags=["System Health"],
)


@router.get("/latest")
def get_latest_health(
    db: Session = Depends(get_db),
):

    return SystemHealthService(db).get_latest_health()


@router.get("/history")
def get_health_history(
    db: Session = Depends(get_db),
):

    return SystemHealthService(db).list_health()


@router.get("/system")
def get_system_health():

    return SystemMonitor().collect()


@router.get("/database")
def get_database_health(
    db: Session = Depends(get_db),
):

    return DatabaseMonitor(db).collect()


@router.get("/ai")
def get_ai_health():

    return AIMonitor().collect()


@router.get("/cameras")
def get_camera_health():

    return CameraMonitor().collect()


@router.get("/all")
def get_complete_health(
    db: Session = Depends(get_db),
):

    return {
        "system": SystemMonitor().collect(),
        "database": DatabaseMonitor(db).collect(),
        "ai": AIMonitor().collect(),
        "cameras": CameraMonitor().collect(),
    }


@router.get("/services")
def get_registered_services():

    return services_health()


@router.get("/live")
async def get_live_services():
    """
    Live health of all microservices.
    """

    return await service_health.check_all()
