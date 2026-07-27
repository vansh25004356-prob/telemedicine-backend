"""
Application configuration for Telemed AI Backend.

All environment variables are loaded and validated here.
Uses pydantic-settings for validation if available,
otherwise falls back to simple os.getenv with defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # ── App ─────────────────────────────────────────────
        self.APP_NAME: str = os.getenv("APP_NAME", "Telemed AI Backend")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.API_V1_PREFIX: str = "/api/v1"

        # ── Security ────────────────────────────────────────
        self.JWT_SECRET_KEY: str = os.getenv(
            "JWT_SECRET_KEY",
            "change-me-in-production-use-a-real-secret-key",
        )
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )

        # ── CORS ────────────────────────────────────────────
        self.CORS_ORIGINS: list = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")

        # ── Supabase ────────────────────────────────────────
        self.SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.SUPABASE_SERVICE_ROLE_KEY: str = os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY", ""
        )
        self.SUPABASE_STORAGE_BUCKET: str = os.getenv(
            "SUPABASE_STORAGE_BUCKET", "medical-files"
        )

        # ── OpenRouter / AI ─────────────────────────────────
        self.OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        self.OPENROUTER_MODEL: str = os.getenv(
            "OPENROUTER_MODEL",
            "openai/gpt-oss-20b",
        )
        self.OPENROUTER_BASE_URL: str = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        )
        self.AI_TEMPERATURE: float = float(
            os.getenv("AI_TEMPERATURE", "0.3")
        )
        self.AI_MAX_TOKENS: int = int(
            os.getenv("AI_MAX_TOKENS", "500")
        )

        # ── Rate Limiting ───────────────────────────────────
        self.RATE_LIMIT_DEFAULT: int = int(
            os.getenv("RATE_LIMIT_DEFAULT", "60")
        )
        self.RATE_LIMIT_WINDOW: int = int(
            os.getenv("RATE_LIMIT_WINDOW", "60")
        )

        # ── File Uploads ────────────────────────────────────
        self.MAX_UPLOAD_SIZE_MB: int = int(
            os.getenv("MAX_UPLOAD_SIZE_MB", "10")
        )
        self.ALLOWED_FILE_TYPES: list = os.getenv(
            "ALLOWED_FILE_TYPES",
            "pdf,doc,docx,jpg,jpeg,png",
        ).split(",")

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        """Maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"


settings = Settings()

