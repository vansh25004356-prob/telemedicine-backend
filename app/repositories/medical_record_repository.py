"""
Medical Records repository - handles all file/medical record operations.

Provides data access for:
- File uploads and metadata storage
- File retrieval (via Supabase Storage)
- File deletion
- File type filtering
"""

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from supabase import Client

from app.core.database import supabase
from app.exceptions import NotFoundException


class MedicalRecordRepository:
    """Repository for medical record (uploaded file) operations."""

    def __init__(self, client: Client = None):
        self.client = client or supabase

    def get_all(self, patient_id: Optional[str] = None) -> list:
        """Fetch all uploaded files, optionally filtered by patient."""
        try:
            query = self.client.table("uploaded_files").select("*")
            if patient_id:
                query = query.eq("patient_id", patient_id)
            response = query.order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching uploaded files: {str(e)}")
            raise

    def get_by_id(self, file_id: str) -> dict:
        """Fetch a single uploaded file by ID."""
        try:
            response = (
                self.client.table("uploaded_files")
                .select("*")
                .eq("id", file_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Medical record", file_id)
            return response.data[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching uploaded file {file_id}: {str(e)}")
            raise

    def get_by_patient_id(self, patient_id: str) -> list:
        """Fetch all uploaded files for a specific patient."""
        return self.get_all(patient_id=patient_id)

    def get_by_consultation_id(self, consultation_id: str) -> list:
        """Fetch all uploaded files for a specific consultation."""
        try:
            response = (
                self.client.table("uploaded_files")
                .select("*")
                .eq("consultation_id", consultation_id)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching files for consultation {consultation_id}: {str(e)}")
            raise

    def create(self, file_data: dict) -> dict:
        """Record a file upload in the database."""
        try:
            response = (
                self.client.table("uploaded_files")
                .insert(file_data)
                .execute()
            )
            logger.info(f"Uploaded file recorded: {response.data[0].get('id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error recording file upload: {str(e)}")
            raise

    def delete(self, file_id: str) -> dict:
        """Delete a file record from the database."""
        try:
            file_record = self.get_by_id(file_id)
            response = (
                self.client.table("uploaded_files")
                .delete()
                .eq("id", file_id)
                .execute()
            )
            if not response.data:
                raise NotFoundException("Medical record", file_id)
            logger.info(f"Deleted file record: {file_id}")
            return {**response.data[0], "storage_path": file_record.get("storage_path")}
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting file record {file_id}: {str(e)}")
            raise

    def delete_from_storage(self, storage_path: str) -> bool:
        """Delete a file from Supabase Storage."""
        try:
            bucket = self.client.storage.from_("medical-files")
            bucket.remove([storage_path])
            logger.info(f"Deleted file from storage: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from storage {storage_path}: {str(e)}")
            return False

    def upload_to_storage(self, file_path: str, file_data: bytes, content_type: str) -> Optional[str]:
        """Upload a file to Supabase Storage."""
        try:
            bucket = self.client.storage.from_("medical-files")
            response = bucket.upload(file_path, file_data, {
                "content-type": content_type,
            })
            logger.info(f"Uploaded file to storage: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error uploading file to storage: {str(e)}")
            return None

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """Get a signed URL for accessing a file."""
        try:
            bucket = self.client.storage.from_("medical-files")
            response = bucket.create_signed_url(storage_path, expires_in)
            return response.get("signedURL") if isinstance(response, dict) else response
        except Exception as e:
            logger.error(f"Error creating signed URL: {str(e)}")
            return None

    def download_from_storage(self, storage_path: str) -> Optional[bytes]:
        """Download a file from Supabase Storage."""
        try:
            bucket = self.client.storage.from_("medical-files")
            response = bucket.download(storage_path)
            return response
        except Exception as e:
            logger.error(f"Error downloading file from storage: {str(e)}")
            return None


# Singleton instance
medical_record_repository = MedicalRecordRepository()

