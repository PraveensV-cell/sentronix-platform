from fastapi import APIRouter
from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.users import router as users_router
from src.api.v1.endpoints.cameras import router as cameras_router
from src.api.v1.endpoints.stream import router as stream_router
from src.api.v1.endpoints.detections import router as detections_router
from src.api.v1.endpoints.alerts import router as alerts_router
from src.api.v1.endpoints.recordings import router as recordings_router
from src.api.routes import recording
from src.api.routes import analytics
from src.api.routes.report import router as report_router
from src.api.routes.audit_export import router as audit_export_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(cameras_router)
api_router.include_router(stream_router)
api_router.include_router(detections_router)
api_router.include_router(alerts_router)
api_router.include_router(recordings_router)
api_router.include_router(recording.router)
api_router.include_router(analytics.router)
api_router.include_router(report_router)
api_router.include_router(audit_export_router)
