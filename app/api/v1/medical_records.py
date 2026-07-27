"""
Medical Records API router - handles all file/medical record endpoints.

Provides:
- GET    /medical-records - List medical records for a patient
- POST   /medical-records/upload - Upload a file
- GET    /medical-records/{id} - Get file details
- GET    /medical-records/{id}/download - Download a file
- DELETE /medical-records/{id} - Delete a file
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from loguru import logger

from app.schemas.common import APIResponse
from app.services.medical_record_service import medical_record_service
from app.core.security import get_current_user
from app.exceptions import NotFoundException, ValidationException

router = APIRouter(
    prefix="/medical-records",
    tags=["Medical Records"],
)


@router.get("/")
async def get_medical_records(
    patient_id: str = Query(..., description="Patient ID"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    consultation_id: Optional[str] = Query(None, description="Filter by consultation ID"),
    current_user: dict = Depends(get_current_user),
):
    """Get medical records/files for a patient."""
    try:
        if consultation_id:
            records = medical_record_service.get_consultation_files(consultation_id)
        elif file_type:
            records = medical_record_service.get_files_by_type(patient_id, file_type)
        else:
            records = medical_record_service.get_patient_files(patient_id)

        return APIResponse(
            success=True,
            message=f"Found {len(records)} records",
            data=records,
        )
    except Exception as e:
        logger.error(f"Error fetching medical records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
    consultation_id: Optional[str] = Form(None),
    uploaded_by: str = Form("patient"),
    current_user: dict = Depends(get_current_user),
):
    """Upload a medical file for a patient."""
    try:
        file_data = await file.read()
        content_type = file.content_type or "application/octet-stream"

        result = medical_record_service.upload_file(
            patient_id=patient_id,
            file_name=file.filename or "unnamed",
            file_data=file_data,
            content_type=content_type,
            consultation_id=consultation_id,
            uploaded_by=uploaded_by,
        )

        logger.info(
            f"User {current_user['id']} uploaded file {file.filename} "
            f"for patient {patient_id}"
        )
        return APIResponse(
            success=True,
            message="File uploaded successfully",
            data=result,
        )
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}")
async def get_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Get details of a specific medical file."""
    try:
        file_record = medical_record_service.get_file(file_id)
        return APIResponse(
            success=True,
            message="File details fetched successfully",
            data=file_record,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/download")
async def download_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Download a medical file."""
    try:
        file_data, file_name, file_type = medical_record_service.download_file(file_id)

        from fastapi.responses import Response
        return Response(
            content=file_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Content-Type": f"application/{file_type}",
            },
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a medical file (DB record + Storage)."""
    try:
        result = medical_record_service.delete_file(file_id)
        logger.info(f"User {current_user['id']} deleted file {file_id}")
        return APIResponse(
            success=True,
            message="File deleted successfully",
            data=result,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

