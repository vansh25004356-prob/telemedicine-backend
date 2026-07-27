"""
Doctor repository - handles all doctor-related database operations.

Provides data access for:
- Doctor profiles CRUD
- Availability management
- Statistics aggregation
- Patient assignments
"""

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from supabase import Client

from app.core.database import supabase
from app.exceptions import NotFoundException


class DoctorRepository:
    """Repository for doctor-related database operations."""

    def __init__(self, client: Client = None):
        self.client = client or supabase

    def get_all(self) -> list:
        """Fetch all doctors."""
        try:
            response = (
                self.client.table("doctors")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching doctors: {str(e)}")
            raise

    def get_by_id(self, doctor_id: str) -> dict:
        """Fetch a single doctor by ID."""
        try:
            response = (
                self.client.table("doctors")
                .select("*")
                .eq("id", doctor_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Doctor", doctor_id)
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching doctor {doctor_id}: {str(e)}")
            raise

    def get_by_auth_user_id(self, auth_user_id: str) -> Optional[dict]:
        """Find a doctor by their auth user ID."""
        try:
            response = (
                self.client.table("doctors")
                .select("*")
                .eq("auth_user_id", auth_user_id)
                .maybe_single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching doctor by auth user ID: {str(e)}")
            return None

    def create(self, doctor_data: dict) -> dict:
        """Create a new doctor profile."""
        try:
            response = (
                self.client.table("doctors")
                .insert(doctor_data)
                .execute()
            )
            logger.info(f"Created doctor profile: {response.data[0].get('id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating doctor: {str(e)}")
            raise

    def update(self, doctor_id: str, doctor_data: dict) -> dict:
        """Update an existing doctor profile."""
        try:
            self.get_by_id(doctor_id)
            response = (
                self.client.table("doctors")
                .update(doctor_data)
                .eq("id", doctor_id)
                .execute()
            )
            logger.info(f"Updated doctor: {doctor_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating doctor {doctor_id}: {str(e)}")
            raise

    def delete(self, doctor_id: str) -> dict:
        """Delete a doctor profile."""
        try:
            response = (
                self.client.table("doctors")
                .delete()
                .eq("id", doctor_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Doctor", doctor_id)
            logger.info(f"Deleted doctor: {doctor_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting doctor {doctor_id}: {str(e)}")
            raise

    def set_availability(self, doctor_id: str, is_available: bool) -> dict:
        """Update doctor availability status."""
        return self.update(doctor_id, {"is_available": is_available})

    def get_available_doctors(self) -> list:
        """Fetch all available doctors."""
        try:
            response = (
                self.client.table("doctors")
                .select("*")
                .eq("is_available", True)
                .order("name")
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching available doctors: {str(e)}")
            raise

    def get_doctor_stats(self, doctor_id: str) -> dict:
        """
        Get statistics for a specific doctor.
        Returns consultation counts, patient counts, etc.
        """
        try:
            # Verify doctor exists
            self.get_by_id(doctor_id)

            # Total consultations
            total = (
                self.client.table("consultations")
                .select("id", count="exact")
                .eq("doctor_id", doctor_id)
                .execute()
            )

            # Active consultations
            active = (
                self.client.table("consultations")
                .select("id", count="exact")
                .eq("doctor_id", doctor_id)
                .eq("status", "active")
                .execute()
            )

            # Completed consultations
            completed = (
                self.client.table("consultations")
                .select("id", count="exact")
                .eq("doctor_id", doctor_id)
                .eq("status", "completed")
                .execute()
            )

            # Weekly consultations
            week_ago = datetime.now(timezone.utc).isoformat()
            weekly = (
                self.client.table("consultations")
                .select("id", count="exact")
                .eq("doctor_id", doctor_id)
                .gte("created_at", week_ago)
                .execute()
            )

            # Unique patients
            patients = (
                self.client.table("consultations")
                .select("patient_id")
                .eq("doctor_id", doctor_id)
                .execute()
            )
            unique_patients = len(set(
                c.get("patient_id") for c in patients.data
            )) if patients.data else 0

            # Today's appointments
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            today_end = datetime.now(timezone.utc).replace(
                hour=23, minute=59, second=59, microsecond=999999
            ).isoformat()
            today_appointments = (
                self.client.table("appointments")
                .select("id", count="exact")
                .eq("doctor_id", doctor_id)
                .gte("scheduled_date", today_start)
                .lte("scheduled_date", today_end)
                .execute()
            )

            return {
                "total_consultations": len(total.data) if total.data else 0,
                "active_consultations": len(active.data) if active.data else 0,
                "completed_consultations": len(completed.data) if completed.data else 0,
                "weekly_consultations": len(weekly.data) if weekly.data else 0,
                "unique_patients": unique_patients,
                "today_appointments": len(today_appointments.data) if today_appointments.data else 0,
            }

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching doctor stats for {doctor_id}: {str(e)}")
            raise

    def get_doctor_notes(self, doctor_id: str, consultation_id: Optional[str] = None) -> list:
        """Get notes created by a doctor, optionally filtered by consultation."""
        try:
            query = (
                self.client.table("doctor_notes")
                .select("*")
                .eq("doctor_id", doctor_id)
            )
            if consultation_id:
                query = query.eq("consultation_id", consultation_id)
            response = query.order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching doctor notes: {str(e)}")
            raise

    def create_note(self, doctor_id: str, consultation_id: str, notes: str, is_private: bool = False) -> dict:
        """Create a doctor note for a consultation."""
        try:
            response = (
                self.client.table("doctor_notes")
                .insert({
                    "doctor_id": doctor_id,
                    "consultation_id": consultation_id,
                    "notes": notes,
                    "is_private": is_private,
                })
                .execute()
            )
            logger.info(f"Doctor note created for consultation {consultation_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating doctor note: {str(e)}")
            raise


# Singleton instance
doctor_repository = DoctorRepository()

