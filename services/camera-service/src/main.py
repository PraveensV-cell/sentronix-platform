from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import api_router
from src.core.config import settings
from src.core.logger import logger
from src.core.startup import startup
from src.core.startup import shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan.
    """

    logger.info("===================================")
    logger.info("Starting Camera Service...")
    logger.info("===================================")

    await startup()

    logger.info("Camera Service Started Successfully.")

    yield

    logger.info("===================================")
    logger.info("Stopping Camera Service...")
    logger.info("===================================")

    await shutdown()

    logger.info("Camera Service Stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SENTRONIX Camera Service",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(
    api_router,
)


@app.get("/")
def root():
    """
    Root endpoint.
    """

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "Running",
    }
