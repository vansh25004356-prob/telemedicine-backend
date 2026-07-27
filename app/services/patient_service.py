"""
Patient service - business logic for patient operations.

Sits between API routers and repositories.
Handles validation, business rules, and coordination.
"""

from loguru import logger

from app.repositories.patient_repository import patient_repository
from app.exceptions import ValidationException, ConflictException


class PatientService:
    """Service layer for patient-related business logic."""

    def get_all_patients(self) -> list:
        """Get all patients."""
        return patient_repository.get_all()

    def get_patient_by_id(self, patient_id: str) -> dict:
        """Get a single patient by ID."""
        return patient_repository.get_by_id(patient_id)

    def create_patient(self, patient_data: dict) -> dict:
        """Create a new patient with validation."""
        # Validate required fields
        required_fields = ["name", "age", "gender"]
        for field in required_fields:
            if field not in patient_data or not patient_data[field]:
                raise ValidationException(f"Missing required field: {field}")

        # Clean phone number if provided
        if patient_data.get("phone"):
            patient_data["phone"] = patient_data["phone"].strip()

        # Create patient
        patient = patient_repository.create(patient_data)
        logger.info(f"Patient created: {patient.get('id')}")
        return patient

    def update_patient(self, patient_id: str, patient_data: dict) -> dict:
        """Update an existing patient."""
        return patient_repository.update(patient_id, patient_data)

    def delete_patient(self, patient_id: str) -> dict:
        """Delete a patient."""
        return patient_repository.delete(patient_id)

    def search_patients(self, query: str) -> list:
        """Search patients by name, phone, or village."""
        if not query or len(query.strip()) < 2:
            raise ValidationException("Search query must be at least 2 characters")
        return patient_repository.search(query.strip())

    def get_patient_summary(self, patient_id: str) -> dict:
        """Get a summary of a patient's consultation history."""
        patient = self.get_patient_by_id(patient_id)
        from app.repositories.consultation_repository import consultation_repository
        consultations = consultation_repository.get_by_patient_id(patient_id)

        return {
            "patient": patient,
            "total_consultations": len(consultations),
            "active_consultations": len(
                [c for c in consultations if c.get("status") == "active"]
            ),
            "completed_consultations": len(
                [c for c in consultations if c.get("status") == "completed"]
            ),
        }


# Singleton instance
patient_service = PatientService()
