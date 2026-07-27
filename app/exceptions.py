"""
Custom exceptions for Telemed AI Backend.

Re-exports from middleware.error_handler for convenience.
"""

from app.middleware.error_handler import (
    AppException,
    NotFoundException,
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ServiceUnavailableException,
)

__all__ = [
    "AppException",
    "NotFoundException",
    "ValidationException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "ServiceUnavailableException",
]

