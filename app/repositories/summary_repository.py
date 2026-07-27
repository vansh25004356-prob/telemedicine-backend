"""
Summary repository - handles all consultation summary database operations.
"""

from loguru import logger

from app.core.database import supabase
from app.exceptions import NotFoundException


class SummaryRepository:
    """Repository for consultation summary-related database operations."""

    def get_by_consultation_id(self, consultation_id: str) -> dict:
        """Fetch summary for a specific consultation."""
        try:
            response = (
                supabase.table("consultation_summaries")
                .select("*")
                .eq("consultation_id", consultation_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Summary", consultation_id)
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Error fetching summary for consultation {consultation_id}: {str(e)}"
            )
            raise

    def create(self, consultation_id: str, summary_data: dict) -> dict:
        """Create a new consultation summary."""
        try:
            data = {
                "consultation_id": consultation_id,
                **summary_data,
            }
            response = (
                supabase.table("consultation_summaries")
                .insert(data)
                .execute()
            )
            logger.info(f"Created summary for consultation {consultation_id}")
            return response.data[0]
        except Exception as e:
            logger.error(
                f"Error creating summary for consultation {consultation_id}: {str(e)}"
            )
            raise

    def update(self, consultation_id: str, summary_data: dict) -> dict:
        """Update an existing consultation summary."""
        try:
            # Check if exists
            self.get_by_consultation_id(consultation_id)

            response = (
                supabase.table("consultation_summaries")
                .update(summary_data)
                .eq("consultation_id", consultation_id)
                .execute()
            )
            logger.info(f"Updated summary for consultation {consultation_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Error updating summary for consultation {consultation_id}: {str(e)}"
            )
            raise

    def exists(self, consultation_id: str) -> bool:
        """Check if a summary exists for a consultation."""
        try:
            response = (
                supabase.table("consultation_summaries")
                .select("id", count="exact")
                .eq("consultation_id", consultation_id)
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False


# Singleton instance
summary_repository = SummaryRepository()

