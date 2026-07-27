"""
Medical Records service - business logic for managing medical files.

Handles:
- File upload validation and processing
- File download with signed URLs
- File deletion (DB record + Storage)
- File type and size validation
"""

import uuid
from typing import Optional

from loguru import logger

from app.repositories.medical_record_repository import medical_record_repository
from app.core.config import settings
from app.exceptions import ValidationException, NotFoundException


class MedicalRecordService:
    """Service layer for medical record/file operations."""

    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png", "gif", "txt"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "image/gif",
        "text/plain",
    }

    def upload_file(
        self,
        patient_id: str,
        file_name: str,
        file_data: bytes,
        content_type: str,
        consultation_id: Optional[str] = None,
        uploaded_by: str = "patient",
    ) -> dict:
        """Upload a file for a patient with validation."""
        # Validate file extension
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationException(
                f"File type '{ext}' is not allowed. "
                f"Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Validate file size
        max_size = settings.MAX_UPLOAD_SIZE_BYTES
        if len(file_data) > max_size:
            max_mb = settings.MAX_UPLOAD_SIZE_MB
            raise ValidationException(
                f"File size exceeds maximum of {max_mb}MB"
            )

        # Generate unique storage path
        file_id = str(uuid.uuid4())
        storage_path = f"patients/{patient_id}/{file_id}/{file_name}"

        # Upload to storage
        uploaded_path = medical_record_repository.upload_to_storage(
            storage_path, file_data, content_type
        )
        if not uploaded_path:
            raise ValidationException("Failed to upload file to storage")

        # Generate signed URL
        signed_url = medical_record_repository.get_signed_url(storage_path)

        # Record in database
        file_record = medical_record_repository.create({
            "patient_id": patient_id,
            "consultation_id": consultation_id,
            "file_name": file_name,
            "file_type": ext,
            "file_size": len(file_data),
            "storage_path": storage_path,
            "signed_url": signed_url,
            "uploaded_by": uploaded_by,
        })

        logger.info(
            f"File uploaded: {file_name} ({ext}, {len(file_data)} bytes) "
            f"for patient {patient_id}"
        )
        return file_record

    def get_patient_files(self, patient_id: str) -> list:
        """Get all files for a patient with refreshed signed URLs."""
        files = medical_record_repository.get_by_patient_id(patient_id)

        # Refresh signed URLs
        for f in files:
            if f.get("storage_path"):
                signed_url = medical_record_repository.get_signed_url(f["storage_path"])
                f["signed_url"] = signed_url

        return files

    def get_consultation_files(self, consultation_id: str) -> list:
        """Get all files for a consultation."""
        return medical_record_repository.get_by_consultation_id(consultation_id)

    def get_file(self, file_id: str) -> dict:
        """Get a single file record with refreshed signed URL."""
        file_record = medical_record_repository.get_by_id(file_id)

        if file_record.get("storage_path"):
            signed_url = medical_record_repository.get_signed_url(file_record["storage_path"])
            file_record["signed_url"] = signed_url

        return file_record

    def download_file(self, file_id: str) -> tuple:
        """Download a file by its ID. Returns (file_data, file_name, content_type)."""
        file_record = medical_record_repository.get_by_id(file_id)
        storage_path = file_record.get("storage_path")

        if not storage_path:
            raise NotFoundException("File storage path")

        file_data = medical_record_repository.download_from_storage(storage_path)
        if not file_data:
            raise NotFoundException("File data not found in storage")

        return file_data, file_record["file_name"], file_record["file_type"]

    def delete_file(self, file_id: str) -> dict:
        """Delete a file (DB record + Storage)."""
        # Get file record (will raise NotFoundException if not exists)
        file_record = medical_record_repository.get_by_id(file_id)

        # Delete from storage
        storage_path = file_record.get("storage_path")
        if storage_path:
            medical_record_repository.delete_from_storage(storage_path)

        # Delete from database
        result = medical_record_repository.delete(file_id)

        logger.info(f"File deleted: {file_record.get('file_name')} (ID: {file_id})")
        return result

    def get_files_by_type(self, patient_id: str, file_type: str) -> list:
        """Get files for a patient filtered by type (e.g., 'pdf', 'image')."""
        files = self.get_patient_files(patient_id)

        if file_type == "image":
            return [f for f in files if f.get("file_type") in ("jpg", "jpeg", "png", "gif")]
        elif file_type == "document":
            return [f for f in files if f.get("file_type") in ("pdf", "doc", "docx", "txt")]

        return [f for f in files if f.get("file_type") == file_type]


# Singleton instance
medical_record_service = MedicalRecordService()

