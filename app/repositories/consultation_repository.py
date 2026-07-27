"""
Consultation repository - handles all consultation database operations.
"""

from typing import Optional

from loguru import logger

from app.core.database import supabase
from app.exceptions import NotFoundException


class ConsultationRepository:
    """Repository for consultation-related database operations."""

    def get_all(self, status: Optional[str] = None) -> list:
        """Fetch all consultations, optionally filtered by status."""
        try:
            query = supabase.table("consultations").select("*")

            if status:
                query = query.eq("status", status)

            response = query.order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching consultations: {str(e)}")
            raise

    def get_by_id(self, consultation_id: str) -> dict:
        """Fetch a single consultation by ID."""
        try:
            response = (
                supabase.table("consultations")
                .select("*")
                .eq("id", consultation_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Consultation", consultation_id)
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching consultation {consultation_id}: {str(e)}")
            raise

    def get_by_patient_id(self, patient_id: str, limit: int = 20) -> list:
        """Fetch consultations for a specific patient."""
        try:
            response = (
                supabase.table("consultations")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching consultations for patient {patient_id}: {str(e)}")
            raise

    def create(self, patient_id: str, status: str = "active") -> dict:
        """Create a new consultation."""
        try:
            response = (
                supabase.table("consultations")
                .insert({
                    "patient_id": patient_id,
                    "status": status,
                })
                .execute()
            )
            logger.info(f"Created consultation: {response.data[0].get('id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            raise

    def update_status(self, consultation_id: str, status: str) -> dict:
        """Update consultation status."""
        try:
            response = (
                supabase.table("consultations")
                .update({"status": status})
                .eq("id", consultation_id)
                .execute()
            )
            logger.info(f"Updated consultation {consultation_id} status to {status}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating consultation {consultation_id}: {str(e)}")
            raise

    def get_by_doctor_id(self, doctor_id: str, status: Optional[str] = None) -> list:
        """Fetch consultations for a specific doctor, optionally filtered by status."""
        try:
            query = supabase.table("consultations").select("*").eq("doctor_id", doctor_id)
            if status:
                query = query.eq("status", status)
            response = query.order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching consultations for doctor {doctor_id}: {str(e)}")
            raise

    def get_today_consultations(self, doctor_id: str) -> list:
        """Fetch today's consultations for a doctor."""
        from datetime import datetime, timezone
        try:
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            today_end = datetime.now(timezone.utc).replace(
                hour=23, minute=59, second=59, microsecond=999999
            ).isoformat()
            response = (
                supabase.table("consultations")
                .select("*")
                .eq("doctor_id", doctor_id)
                .gte("created_at", today_start)
                .lte("created_at", today_end)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching today's consultations for doctor {doctor_id}: {str(e)}")
            raise

    def assign_doctor(self, consultation_id: str, doctor_id: str) -> dict:
        """Assign a doctor to a consultation."""
        try:
            response = (
                supabase.table("consultations")
                .update({"doctor_id": doctor_id})
                .eq("id", consultation_id)
                .execute()
            )
            logger.info(f"Assigned doctor {doctor_id} to consultation {consultation_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error assigning doctor: {str(e)}")
            raise

    def update_consultation(self, consultation_id: str, data: dict) -> dict:
        """Update consultation details (diagnosis, notes, treatment plan, etc.)."""
        try:
            self.get_by_id(consultation_id)
            response = (
                supabase.table("consultations")
                .update(data)
                .eq("id", consultation_id)
                .execute()
            )
            logger.info(f"Updated consultation {consultation_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating consultation {consultation_id}: {str(e)}")
            raise

    def get_active_consultations(self) -> list:
        """Fetch all active consultations."""
        return self.get_all(status="active")

    def get_completed_consultations(self) -> list:
        """Fetch all completed consultations."""
        return self.get_all(status="completed")


# Singleton instance
consultation_repository = ConsultationRepository()

