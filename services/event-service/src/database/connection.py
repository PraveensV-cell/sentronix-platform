from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings


DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+psycopg2",
    "postgresql+asyncpg",
)


engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
