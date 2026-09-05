from __future__ import annotations

from src.core.logger import logger


async def startup() -> None:
    """
    Event Service startup tasks.
    """

    logger.info(
        "Initializing Event Service...",
    )

    # Future:
    # - Database connection
    # - Message broker connection
    # - External service checks

    logger.success(
        "Event Service Started Successfully.",
    )


async def shutdown() -> None:
    """
    Event Service shutdown tasks.
    """

    logger.info(
        "Stopping Event Service...",
    )

    # Future:
    # - Close database connection
    # - Close HTTP clients
    # - Flush queues

    logger.success(
        "Event Service Shutdown Complete.",
    )
