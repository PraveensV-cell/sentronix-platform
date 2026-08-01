from src.api.router import api_router
from src.api.routes.ai import (
    router as ai_router,
)

__all__ = [
    "api_router",
]
api_router.include_router(
    ai_router,
)
