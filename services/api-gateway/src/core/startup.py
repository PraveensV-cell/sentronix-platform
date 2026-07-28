from sqlalchemy import text

from src.core.logger import logger
from src.database.base import Base
from src.database.session import SessionLocal, engine

# Import every model so SQLAlchemy registers them
from src.models import *  # noqa: F401,F403


async def startup() -> None:
    """
    Application startup.
    """

    logger.info("Initializing database...")

    # Create all missing tables
    Base.metadata.create_all(bind=engine)

    logger.info("Database tables verified.")

    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
        db.commit()
        logger.info("Database connection successful.")
    finally:
        db.close()


async def shutdown() -> None:
    """
    Application shutdown.
    """

    logger.info("Application shutdown complete.")
