"""
Appointment repository - handles all appointment database operations.

Provides data access for:
- Appointment CRUD
- Status management
- Calendar queries
- Doctor/Patient schedule
"""

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from supabase import Client

from app.core.database import supabase
from app.exceptions import NotFoundException


class AppointmentRepository:
    """Repository for appointment-related database operations."""

    def __init__(self, client: Client = None):
        self.client = client or supabase

    def get_all(self, status: Optional[str] = None) -> list:
        """Fetch all appointments, optionally filtered by status."""
        try:
            query = self.client.table("appointments").select("*")
            if status:
                query = query.eq("status", status)
            response = query.order("scheduled_date", desc=False).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching appointments: {str(e)}")
            raise

    def get_by_id(self, appointment_id: str) -> dict:
        """Fetch a single appointment by ID."""
        try:
            response = (
                self.client.table("appointments")
                .select("*")
                .eq("id", appointment_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Appointment", appointment_id)
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching appointment {appointment_id}: {str(e)}")
            raise

    def get_by_patient_id(self, patient_id: str, status: Optional[str] = None) -> list:
        """Fetch appointments for a specific patient."""
        try:
            query = (
                self.client.table("appointments")
                .select("*")
                .eq("patient_id", patient_id)
            )
            if status:
                query = query.eq("status", status)
            response = query.order("scheduled_date", desc=False).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching appointments for patient {patient_id}: {str(e)}")
            raise

    def get_by_doctor_id(self, doctor_id: str, status: Optional[str] = None) -> list:
        """Fetch appointments for a specific doctor."""
        try:
            query = (
                self.client.table("appointments")
                .select("*")
                .eq("doctor_id", doctor_id)
            )
            if status:
                query = query.eq("status", status)
            response = query.order("scheduled_date", desc=False).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching appointments for doctor {doctor_id}: {str(e)}")
            raise

    def get_upcoming(self, limit: int = 10) -> list:
        """Fetch upcoming appointments (scheduled or confirmed)."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            response = (
                self.client.table("appointments")
                .select("*")
                .in_("status", ["scheduled", "confirmed"])
                .gte("scheduled_date", now)
                .order("scheduled_date", desc=False)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching upcoming appointments: {str(e)}")
            raise

    def create(self, appointment_data: dict) -> dict:
        """Create a new appointment."""
        try:
            response = (
                self.client.table("appointments")
                .insert(appointment_data)
                .execute()
            )
            logger.info(f"Created appointment: {response.data[0].get('id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            raise

    def update(self, appointment_id: str, appointment_data: dict) -> dict:
        """Update an existing appointment."""
        try:
            self.get_by_id(appointment_id)
            response = (
                self.client.table("appointments")
                .update(appointment_data)
                .eq("id", appointment_id)
                .execute()
            )
            logger.info(f"Updated appointment: {appointment_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
            raise

    def update_status(self, appointment_id: str, status: str) -> dict:
        """Update appointment status."""
        return self.update(appointment_id, {"status": status})

    def delete(self, appointment_id: str) -> dict:
        """Delete an appointment."""
        try:
            response = (
                self.client.table("appointments")
                .delete()
                .eq("id", appointment_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Appointment", appointment_id)
            logger.info(f"Deleted appointment: {appointment_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting appointment {appointment_id}: {str(e)}")
            raise

    def get_calendar(self, doctor_id: str, start_date: str, end_date: str) -> list:
        """Get appointments for a doctor within a date range for calendar view."""
        try:
            response = (
                self.client.table("appointments")
                .select("*")
                .eq("doctor_id", doctor_id)
                .gte("scheduled_date", start_date)
                .lte("scheduled_date", end_date)
                .order("scheduled_date", desc=False)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching calendar appointments: {str(e)}")
            raise


# Singleton instance
appointment_repository = AppointmentRepository()

