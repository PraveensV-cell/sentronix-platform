from __future__ import annotations

import asyncio
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
    startup,
    shutdown,
)
from src.services.camera_client import (
    camera_client,
)
from src.services.event_client import (
    event_client,
)
from src.workers.detection_worker import (
    detection_worker,
)


worker_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """
    Application lifespan.
    """

    global worker_task

    logger.info(
        "Starting AI Detection Service...",
    )

    await startup()

    worker_task = asyncio.create_task(
        detection_worker.start(),
    )

    logger.info(
        "Detection Worker Started.",
    )

    yield

    logger.info(
        "Stopping AI Detection Service...",
    )

    await detection_worker.stop()

    if worker_task:
        worker_task.cancel()

        try:
            await worker_task

        except asyncio.CancelledError:
            pass

    await event_client.close()

    await camera_client.close()

    await shutdown()

    logger.info(
        "AI Detection Service Stopped.",
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
def root():
    """
    Root endpoint.
    """

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


logger.info(
    "AI Detection Service Initialized",
)
