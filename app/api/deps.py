"""
Shared FastAPI dependencies for Telemed AI Backend.

Provides dependency injection for:
- Database sessions
- Authentication
- Rate limiting
- Pagination
"""

from typing import Optional

from fastapi import Depends, Query

from app.core.security import get_current_user, get_current_doctor


class PaginationParams:
    """Pagination dependency."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page


class SearchParams:
    """Search query parameters dependency."""

    def __init__(
        self,
        q: Optional[str] = Query(None, description="Search query"),
        status: Optional[str] = Query(None, description="Filter by status"),
    ):
        self.query = q
        self.status = status


# Re-export auth dependencies for convenience
__all__ = [
    "get_current_user",
    "get_current_doctor",
    "PaginationParams",
    "SearchParams",
]
