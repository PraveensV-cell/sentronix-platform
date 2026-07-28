from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.router import api_router
from src.core.config import settings
from src.core.logger import logger
from src.core.startup import shutdown, startup
from src.api.routes.detect import router as detect_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan.
    """

    await startup()

    yield

    await shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/")
def root():
    """
    Root endpoint.
    """

    return {
        "message": "Sentronix AI Detection Service",
        "status": "running",
    }


logger.info("AI Detection Service Initialized")

app.include_router(detect_router)
