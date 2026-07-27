"""
Doctor service - business logic for doctor-related operations.

Handles:
- Doctor profile management
- Availability management
- Consultation assignments
- Doctor notes
- Statistics and analytics
"""

from typing import Optional

from loguru import logger

from app.repositories.doctor_repository import doctor_repository
from app.repositories.consultation_repository import consultation_repository
from app.repositories.patient_repository import patient_repository
from app.exceptions import ValidationException, NotFoundException


class DoctorService:
    """Service layer for doctor-related business logic."""

    def get_profile(self, doctor_id: str) -> dict:
        """Get doctor profile by ID."""
        return doctor_repository.get_by_id(doctor_id)

    def get_profile_by_auth_id(self, auth_user_id: str) -> dict:
        """Get doctor profile by auth user ID."""
        doctor = doctor_repository.get_by_auth_user_id(auth_user_id)
        if not doctor:
            raise NotFoundException("Doctor profile", auth_user_id)
        return doctor

    def create_profile(self, doctor_data: dict) -> dict:
        """Create a new doctor profile."""
        return doctor_repository.create(doctor_data)

    def update_profile(self, doctor_id: str, doctor_data: dict) -> dict:
        """Update doctor profile."""
        return doctor_repository.update(doctor_id, doctor_data)

    def toggle_availability(self, doctor_id: str, is_available: bool) -> dict:
        """Toggle doctor availability."""
        return doctor_repository.set_availability(doctor_id, is_available)

    def get_available_doctors(self) -> list:
        """Get all available doctors."""
        return doctor_repository.get_available_doctors()

    def get_consultations(self, doctor_id: str, status: Optional[str] = None) -> list:
        """
        Get consultations assigned to a doctor.
        If status is provided, filter by status.
        """
        doctor = doctor_repository.get_by_id(doctor_id)
        consultations = consultation_repository.get_by_doctor_id(doctor_id, status)

        # Enrich with patient info
        enriched = []
        for c in consultations:
            try:
                patient = patient_repository.get_by_id(c["patient_id"])
                enriched.append({**c, "patient": patient})
            except NotFoundException:
                enriched.append({**c, "patient": None})

        return enriched

    def get_stats(self, doctor_id: str) -> dict:
        """Get comprehensive statistics for a doctor."""
        return doctor_repository.get_doctor_stats(doctor_id)

    def create_note(self, doctor_id: str, consultation_id: str, notes: str, is_private: bool = False) -> dict:
        """Create a doctor note for a consultation."""
        return doctor_repository.create_note(doctor_id, consultation_id, notes, is_private)

    def get_notes(self, doctor_id: str, consultation_id: Optional[str] = None) -> list:
        """Get notes for a doctor, optionally filtered by consultation."""
        return doctor_repository.get_doctor_notes(doctor_id, consultation_id)

    def get_dashboard(self, doctor_id: str) -> dict:
        """
        Get comprehensive dashboard data for a doctor.
        Combines stats, active consultations, and recent activity.
        """
        doctor = doctor_repository.get_by_id(doctor_id)
        stats = self.get_stats(doctor_id)
        active_consultations = consultation_repository.get_by_doctor_id(doctor_id, "active")

        today_consultations = consultation_repository.get_today_consultations(doctor_id)

        return {
            "doctor": doctor,
            "stats": stats,
            "active_consultations": active_consultations,
            "active_count": len(active_consultations),
            "today_consultations": today_consultations,
            "today_count": len(today_consultations),
        }


# Singleton instance
doctor_service = DoctorService()

