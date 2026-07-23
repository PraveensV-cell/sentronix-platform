import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logger import app_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming request and outgoing response.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        app_logger.info(f"Incoming Request | {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = round((time.time() - start_time) * 1000, 2)

        app_logger.info(
            f"Completed | Status={response.status_code} | Time={process_time} ms"
        )

        return response
