from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.router import api_router
from src.core.startup import startup, shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()

    yield

    await shutdown()


app = FastAPI(
    title="SENTRONIX API Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
