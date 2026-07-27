"""
Request/Response logging middleware for Telemed AI Backend.

Logs:
- All incoming requests with method, path, client IP
- Response status codes
- Request duration
- Slow request warnings
"""

import time
import uuid

from fastapi import FastAPI, Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all incoming requests and their responses.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.slow_request_threshold = 5.0  # seconds

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host

        # Log incoming request
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"from {client_ip}"
        )

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] ✗ {request.method} {request.url.path} "
                f"FAILED after {duration:.3f}s: {str(e)}"
            )
            raise

        duration = time.time() - start_time

        # Log response
        log_level = logger.info
        if duration > self.slow_request_threshold:
            log_level = logger.warning
            log_level(
                f"[{request_id}] ← {request.method} {request.url.path} "
                f"{response.status_code} SLOW ({duration:.3f}s)"
            )
        elif response.status_code >= 500:
            log_level = logger.error
        elif response.status_code >= 400:
            log_level = logger.warning

        log_level(
            f"[{request_id}] ← {request.method} {request.url.path} "
            f"{response.status_code} ({duration:.3f}s)"
        )

        # Add request ID header to response
        response.headers["X-Request-ID"] = request_id

        return response

