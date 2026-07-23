import time

from fastapi import Request

from src.core.logger import logger


class RequestLoggingMiddleware:
    """
    Enterprise request logging middleware.
    """

    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = round((time.time() - start_time) * 1000, 2)

        logger.info(
            "%s | %s | %s | %s | %.2f ms",
            request.client.host,
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )

        return response
