"""
Telemed AI Backend - Main Application Entry Point

FastAPI application with:
- Modular architecture (routers, services, repositories)
- Global exception handlers
- Request logging
- Rate limiting
- CORS configuration
- Health and version endpoints
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import db
from app.core.logging import setup_logging
from app.middleware.error_handler import setup_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.services.ai_service import test_ai_connection

# ── API Router Imports ────────────────────────────────────
from app.api.v1.appointments import router as appointment_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.doctors import router as doctor_router
from app.api.v1.medical_records import router as medical_record_router
from app.api.v1.patients import router as patient_router
from app.api.v1.summaries import router as summary_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode")

    # Health checks
    db_healthy = db.health_check()
    if not db_healthy:
        logger.warning("Database connection failed on startup")

    ai_healthy = await test_ai_connection()
    if not ai_healthy:
        logger.warning("AI service connection failed on startup")

    logger.info(f"Database: {'connected' if db_healthy else 'disconnected'}")
    logger.info(f"AI Service: {'available' if ai_healthy else 'unavailable'}")

    yield

    # Shutdown
    logger.info("Shutting down Telemed AI Backend")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production-ready AI Telemedicine Platform API",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Global exception handlers
setup_exception_handlers(app)


# ── Health & Version Endpoints ────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint - used by monitoring systems."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected" if db.health_check() else "disconnected",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/version")
async def version_info():
    """Get API version information."""
    import sys
    return {
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "python_version": sys.version.split()[0],
        "api_version": "v1",
    }


# ── Router Registration ───────────────────────────────────

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(patient_router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor_router, prefix=settings.API_V1_PREFIX)
app.include_router(appointment_router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_record_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(summary_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint - API status."""
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
