"""
Database configuration for Telemed AI Backend.

Provides:
- Supabase client singleton (both service role and anon)
- Async-compatible helpers
- Connection health check

Gracefully handles missing configuration by allowing None clients,
which lets the app start in development without a database connection.
"""

from typing import Optional

from loguru import logger
from supabase import Client, create_client

from app.core.config import settings


class Database:
    """Database manager providing Supabase clients."""

    def __init__(self):
        self._service_client: Optional[Client] = None
        self._anon_client: Optional[Client] = None

    @property
    def service(self) -> Optional[Client]:
        """Get service role client (admin access). Returns None if not configured."""
        if self._service_client is not None:
            return self._service_client

        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("Supabase service client not configured (SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing)")
            return None

        try:
            self._service_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
            logger.debug("Supabase service client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase service client: {str(e)}")
            return None

        return self._service_client

    @property
    def anon(self) -> Optional[Client]:
        """Get anon client (limited access for frontend). Returns None if not configured."""
        if self._anon_client is not None:
            return self._anon_client

        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.warning("Supabase anon client not configured (SUPABASE_URL or SUPABASE_ANON_KEY missing)")
            return None

        try:
            self._anon_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,
            )
            logger.debug("Supabase anon client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase anon client: {str(e)}")
            return None

        return self._anon_client

    def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        client = self.service
        if client is None:
            return False
        try:
            client.table("patients").select("id", count="exact").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Singleton instance
db = Database()


def get_supabase() -> Optional[Client]:
    """Get the Supabase service client. Returns None if not configured."""
    return db.service


# Backward compatibility alias - lazy accessor that returns None if not configured
@property
def _supabase_alias(self) -> Optional[Client]:
    return db.service


# Module-level lazy accessor
class _SupabaseAccessor:
    """Lazy accessor for backward-compatible supabase import."""
    
    def __getattr__(self, name):
        client = db.service
        if client is None:
            raise RuntimeError(
                "Supabase is not configured. Please set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY in your .env file."
            )
        return getattr(client, name)


supabase = _SupabaseAccessor()

