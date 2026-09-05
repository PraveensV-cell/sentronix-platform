from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.router import (
    api_router,
)
from src.core.config import (
    settings,
)
from src.core.logger import (
    logger,
)
from src.core.startup import (
    shutdown,
    startup,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """
    Application lifecycle management.
    """

    logger.info(
        "Starting Event Service...",
    )

    await startup()

    logger.success(
        "Event Service started.",
    )

    yield

    logger.info(
        "Stopping Event Service...",
    )

    await shutdown()

    logger.success(
        "Event Service stopped.",
    )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


app.include_router(
    api_router,
)


@app.get("/")
async def root():
    """
    Root endpoint.
    """

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }
