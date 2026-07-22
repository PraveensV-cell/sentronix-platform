from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.logger import logger
from src.core.startup import startup, shutdown
from src.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    """

    logger.info("Starting SENTRONIX API Gateway...")

    await startup()

    logger.info("API Gateway Started Successfully")

    yield

    logger.info("API Gateway Shutting Down")

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

# Register Global Exception Handlers
register_exception_handlers(app)

# Register API Routes
app.include_router(api_router)
