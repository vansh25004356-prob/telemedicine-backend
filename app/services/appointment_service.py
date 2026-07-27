"""
Appointment service - business logic for appointment operations.

Handles:
- Appointment booking and scheduling
- Status management (cancel, reschedule, confirm)
- Calendar queries
- Conflict detection
"""

from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.repositories.appointment_repository import appointment_repository
from app.repositories.patient_repository import patient_repository
from app.repositories.doctor_repository import doctor_repository
from app.exceptions import ValidationException, NotFoundException


class AppointmentService:
    """Service layer for appointment-related business logic."""

    def book_appointment(self, appointment_data: dict) -> dict:
        """Book a new appointment with validation."""
        # Validate required fields
        required_fields = ["patient_id", "doctor_id", "scheduled_date", "reason"]
        for field in required_fields:
            if field not in appointment_data or not appointment_data[field]:
                raise ValidationException(f"Missing required field: {field}")

        # Verify patient exists
        patient_repository.get_by_id(appointment_data["patient_id"])

        # Verify doctor exists and is available
        doctor = doctor_repository.get_by_id(appointment_data["doctor_id"])

        # Ensure scheduled_date is in the future
        scheduled = appointment_data["scheduled_date"]
        if isinstance(scheduled, str):
            scheduled = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
        if scheduled <= datetime.now(timezone.utc):
            raise ValidationException("Appointment must be scheduled in the future")

        # Create appointment
        appointment = appointment_repository.create(appointment_data)
        logger.info(
            f"Appointment booked: {appointment.get('id')} "
            f"for patient {appointment_data['patient_id']} "
            f"with doctor {appointment_data['doctor_id']}"
        )
        return appointment

    def cancel_appointment(self, appointment_id: str) -> dict:
        """Cancel an appointment."""
        appointment = appointment_repository.get_by_id(appointment_id)

        if appointment["status"] in ("cancelled", "completed"):
            raise ValidationException(
                f"Cannot cancel appointment with status: {appointment['status']}"
            )

        result = appointment_repository.update_status(appointment_id, "cancelled")
        logger.info(f"Appointment {appointment_id} cancelled")
        return result

    def reschedule_appointment(self, appointment_id: str, new_date: str) -> dict:
        """Reschedule an appointment to a new date/time."""
        appointment = appointment_repository.get_by_id(appointment_id)

        if appointment["status"] in ("cancelled", "completed"):
            raise ValidationException(
                f"Cannot reschedule appointment with status: {appointment['status']}"
            )

        # Validate new date is in the future
        new_scheduled = datetime.fromisoformat(new_date.replace("Z", "+00:00"))
        if new_scheduled <= datetime.now(timezone.utc):
            raise ValidationException("New appointment time must be in the future")

        result = appointment_repository.update(appointment_id, {
            "scheduled_date": new_date,
            "status": "scheduled",
        })
        logger.info(f"Appointment {appointment_id} rescheduled to {new_date}")
        return result

    def confirm_appointment(self, appointment_id: str) -> dict:
        """Confirm a scheduled appointment."""
        appointment = appointment_repository.get_by_id(appointment_id)

        if appointment["status"] != "scheduled":
            raise ValidationException(
                f"Cannot confirm appointment with status: {appointment['status']}"
            )

        result = appointment_repository.update_status(appointment_id, "confirmed")
        logger.info(f"Appointment {appointment_id} confirmed")
        return result

    def complete_appointment(self, appointment_id: str) -> dict:
        """Mark an appointment as completed."""
        result = appointment_repository.update_status(appointment_id, "completed")
        logger.info(f"Appointment {appointment_id} completed")
        return result

    def mark_no_show(self, appointment_id: str) -> dict:
        """Mark an appointment as no-show."""
        result = appointment_repository.update_status(appointment_id, "no_show")
        logger.info(f"Appointment {appointment_id} marked as no-show")
        return result

    def get_appointment(self, appointment_id: str) -> dict:
        """Get appointment details with related info."""
        appointment = appointment_repository.get_by_id(appointment_id)

        # Enrich with patient and doctor info
        try:
            patient = patient_repository.get_by_id(appointment["patient_id"])
            appointment["patient"] = patient
        except NotFoundException:
            appointment["patient"] = None

        try:
            doctor = doctor_repository.get_by_id(appointment["doctor_id"])
            appointment["doctor"] = doctor
        except NotFoundException:
            appointment["doctor"] = None

        return appointment

    def get_patient_appointments(self, patient_id: str, status: Optional[str] = None) -> list:
        """Get appointments for a patient."""
        return appointment_repository.get_by_patient_id(patient_id, status)

    def get_doctor_appointments(self, doctor_id: str, status: Optional[str] = None) -> list:
        """Get appointments for a doctor."""
        return appointment_repository.get_by_doctor_id(doctor_id, status)

    def get_upcoming(self, limit: int = 10) -> list:
        """Get upcoming appointments."""
        return appointment_repository.get_upcoming(limit)

    def get_calendar(self, doctor_id: str, start_date: str, end_date: str) -> list:
        """Get appointments for calendar view."""
        return appointment_repository.get_calendar(doctor_id, start_date, end_date)


# Singleton instance
appointment_service = AppointmentService()

