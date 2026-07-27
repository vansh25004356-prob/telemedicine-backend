"""
Logging configuration for Telemed AI Backend.

Provides structured logging with:
- Console output
- File rotation
- Request ID tracking
- Different log levels per environment
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings


class LogConfig:
    """Centralized logging configuration."""

    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.LOG_LEVEL.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler with rotation
    logger.add(
        LOG_DIR / "telemed_{time:YYYY-MM-DD}.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=False,
    )

    # Error file handler
    logger.add(
        LOG_DIR / "telemed_error_{time:YYYY-MM-DD}.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )


def setup_logging():
    """Initialize logging configuration."""
    LogConfig()
    logger.info("Logging initialized")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")


def get_logger(module_name: Optional[str] = None):
    """Get a logger instance with optional module name."""
    return logger.bind(module=module_name or "telemed")

