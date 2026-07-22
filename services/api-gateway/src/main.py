from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.startup import shutdown, startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    """

    await startup()

    yield

    await shutdown()


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

app.include_router(api_router)
