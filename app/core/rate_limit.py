"""
Rate limiting middleware for Telemed AI Backend.

Provides:
- In-memory rate limiting per IP
- Configurable limits per endpoint
- Rate limit headers in responses
"""

import time
from collections import defaultdict
from typing import Callable, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class RateLimitEntry:
    """Represents a rate limit entry for a single IP/endpoint combination."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: list[float] = []

    def is_allowed(self) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        Returns (allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Remove old timestamps
        self.timestamps = [t for t in self.timestamps if t > window_start]

        if len(self.timestamps) >= self.max_requests:
            retry_after = int(self.timestamps[0] - window_start)
            return False, max(1, retry_after)

        self.timestamps.append(now)
        return True, 0


class RateLimitConfig:
    """Configuration for rate limits on different path patterns."""

    def __init__(self):
        self.default_limit = settings.RATE_LIMIT_DEFAULT
        self.default_window = settings.RATE_LIMIT_WINDOW
        self.endpoint_limits: Dict[str, Tuple[int, int]] = {
            # path_prefix: (max_requests, window_seconds)
            "/api/v1/chat/message": (10, 60),       # 10 messages per minute
            "/api/v1/chat/start": (5, 60),           # 5 consultations per minute
            "/api/v1/chat/end": (5, 60),             # 5 ends per minute
            "/api/v1/patients/": (30, 60),           # 30 patient ops per minute
            "/api/v1/auth/": (5, 60),                # 5 auth attempts per minute
            "/api/v1/summaries/": (10, 60),          # 10 summary requests per minute
            "/health": (60, 60),                     # 60 health checks per minute
            "/api/v1/chat/test": (3, 60),            # 3 test requests per minute
        }

    def get_limits(self, path: str) -> Tuple[int, int]:
        """Get rate limits for a specific path."""
        for prefix, limits in self.endpoint_limits.items():
            if path.startswith(prefix):
                return limits
        return self.default_limit, self.default_window


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies rate limiting based on client IP.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.config = RateLimitConfig()
        self.store: Dict[str, RateLimitEntry] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for non-API routes
        if not request.url.path.startswith("/api/") and not request.url.path == "/health":
            return await call_next(request)

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
        client_ip = client_ip or "unknown"

        # Get rate limits for this path
        max_requests, window_seconds = self.config.get_limits(request.url.path)

        # Create store key
        store_key = f"{client_ip}:{request.method}:{request.url.path}"

        # Check rate limit
        if store_key not in self.store:
            self.store[store_key] = RateLimitEntry(max_requests, window_seconds)

        allowed, retry_after = self.store[store_key].is_allowed()

        # Add rate limit headers
        response = await call_next(request)

        if isinstance(response, Response):
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, max_requests - len(self.store[store_key].timestamps))
            )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return response

