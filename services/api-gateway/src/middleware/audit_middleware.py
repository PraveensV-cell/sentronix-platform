import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.database.session import SessionLocal
from src.utils.audit_logger import audit_logger


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically records
    every incoming API request.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.time()

        response = await call_next(request)

        process_time = round(
            time.time() - start_time,
            4,
        )

        # Ignore documentation endpoints
        ignored_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        if request.url.path not in ignored_paths:
            db = SessionLocal()

            try:
                user_id = None

                # If authentication stores the user
                # inside request.state.current_user
                if hasattr(request.state, "current_user"):
                    current_user = request.state.current_user

                    if current_user:
                        user_id = current_user.id

                audit_logger.log(
                    db=db,
                    user_id=user_id,
                    action=request.method,
                    resource=request.url.path,
                    description=(
                        f"{request.method} "
                        f"{request.url.path} "
                        f"({response.status_code}) "
                        f"{process_time}s"
                    ),
                    ip_address=request.client.host if request.client else None,
                )

            finally:
                db.close()

        return response
