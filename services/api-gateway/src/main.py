from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.ai_analytics import (
    router as ai_analytics_router,
)
from src.api.routes.analytics import (
    router as analytics_router,
)
from src.api.routes.audit_export import (
    router as audit_export_router,
)
from src.api.routes.audit_log import (
    router as audit_log_router,
)
from src.api.routes.camera_analytics import (
    router as camera_analytics_router,
)
from src.api.routes.dashboard import (
    router as dashboard_router,
)
from src.api.routes.integration.ai import (
    router as ai_integration_router,
)
from src.api.routes.report import (
    router as report_router,
)
from src.api.routes.system_health import (
    router as system_health_router,
)
from src.api.routes.ai_proxy import (
    router as ai_proxy_router,
)
from src.api.v1.router import api_router
from src.core.config import settings
from src.core.logger import logger
from src.core.startup import shutdown
from src.core.startup import startup
from src.exceptions.handlers import register_exception_handlers
from src.middleware.audit_middleware import AuditMiddleware
from src.middleware.logging import LoggingMiddleware
from src.websocket.routes import (
    router as websocket_router,
)
from src.workers.system_health_worker import (
    system_health_worker,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("====================================")
    logger.info("Starting SENTRONIX API Gateway...")
    logger.info("====================================")

    await startup()

    try:
        system_health_worker.start()
        logger.info("System Health Worker Started")
    except Exception as exc:
        logger.exception(
            "Failed to start System Health Worker: %s",
            exc,
        )

    logger.info("API Gateway Started Successfully")

    yield

    logger.info("====================================")
    logger.info("Shutting Down SENTRONIX API Gateway...")
    logger.info("====================================")

    try:
        system_health_worker.stop()
        logger.info("System Health Worker Stopped")
    except Exception as exc:
        logger.exception(
            "Failed to stop System Health Worker: %s",
            exc,
        )

    await shutdown()

    logger.info("API Gateway Shutdown Complete")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.API_DESCRIPTION,
    version=settings.APP_VERSION,
    contact={
        "name": settings.CONTACT_NAME,
        "email": settings.CONTACT_EMAIL,
    },
    license_info={
        "name": settings.LICENSE_NAME,
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(LoggingMiddleware)
app.add_middleware(AuditMiddleware)


register_exception_handlers(app)


app.include_router(api_router)
app.include_router(websocket_router)

app.include_router(report_router)

app.include_router(audit_log_router)
app.include_router(audit_export_router)

app.include_router(system_health_router)

app.include_router(dashboard_router)
app.include_router(analytics_router)
app.include_router(ai_analytics_router)
app.include_router(camera_analytics_router)

# ===========================
# AI Service Integration
# ===========================
app.include_router(ai_integration_router)
app.include_router(ai_proxy_router)
