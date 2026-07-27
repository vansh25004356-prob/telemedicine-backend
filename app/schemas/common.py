"""
Common/shared schemas for Telemed AI Backend.
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = 1
    per_page: int = 20


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    success: bool = True
    message: str = "Success"
    data: list = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 0


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "Success"
    data: Any = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    detail: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    ai_service: str = "available"


class VersionResponse(BaseModel):
    """Version information response."""
    version: str
    environment: str
    python_version: str
    api_version: str = "v1"

