"""
Patient repository - handles all patient database operations.

Follows the Repository pattern to abstract database access.
All Supabase queries for patients go through this module.
"""

from typing import Optional

from loguru import logger
from supabase import Client

from app.core.database import supabase
from app.exceptions import NotFoundException


class PatientRepository:
    """Repository for patient-related database operations."""

    def __init__(self, client: Client = None):
        self.client = client or supabase

    def get_all(self) -> list:
        """Fetch all patients ordered by creation date descending."""
        try:
            response = (
                self.client.table("patients")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching patients: {str(e)}")
            raise

    def get_by_id(self, patient_id: str) -> dict:
        """Fetch a single patient by ID."""
        try:
            response = (
                self.client.table("patients")
                .select("*")
                .eq("id", patient_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Patient", patient_id)
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching patient {patient_id}: {str(e)}")
            raise

    def create(self, patient_data: dict) -> dict:
        """Create a new patient record."""
        try:
            response = (
                self.client.table("patients")
                .insert(patient_data)
                .execute()
            )
            logger.info(f"Created patient: {response.data[0].get('id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}")
            raise

    def update(self, patient_id: str, patient_data: dict) -> dict:
        """Update an existing patient record."""
        try:
            # Verify patient exists
            self.get_by_id(patient_id)

            response = (
                self.client.table("patients")
                .update(patient_data)
                .eq("id", patient_id)
                .execute()
            )
            logger.info(f"Updated patient: {patient_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {str(e)}")
            raise

    def delete(self, patient_id: str) -> dict:
        """Delete a patient record."""
        try:
            response = (
                self.client.table("patients")
                .delete()
                .eq("id", patient_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Patient", patient_id)
            logger.info(f"Deleted patient: {patient_id}")
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting patient {patient_id}: {str(e)}")
            raise

    def search(self, query: str) -> list:
        """Search patients by name, phone, or village."""
        try:
            response = (
                self.client.table("patients")
                .select("*")
                .or_(
                    f"name.ilike.%{query}%,"
                    f"phone.ilike.%{query}%,"
                    f"village.ilike.%{query}%"
                )
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error searching patients: {str(e)}")
            raise

    def get_by_phone(self, phone: str) -> Optional[dict]:
        """Find a patient by phone number."""
        try:
            response = (
                self.client.table("patients")
                .select("*")
                .eq("phone", phone)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching patient by phone: {str(e)}")
            raise


# Singleton instance
patient_repository = PatientRepository()

