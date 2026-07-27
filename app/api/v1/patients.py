"""
Patient API router - handles all patient-related endpoints.

Uses the PatientService for business logic and PatientRepository for data access.
"""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.schemas.patient import PatientCreate
from app.schemas.common import APIResponse
from app.services.patient_service import patient_service
from app.exceptions import NotFoundException, ValidationException

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


@router.get("/")
async def get_patients(search: str = Query(None, description="Search query")):
    """Get all patients, optionally filtered by search query."""
    try:
        if search:
            patients = patient_service.search_patients(search)
            message = f"Found {len(patients)} patients matching '{search}'"
        else:
            patients = patient_service.get_all_patients()
            message = "Patients fetched successfully"

        return APIResponse(
            success=True,
            message=message,
            data=patients,
        )
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}")
async def get_patient(patient_id: str):
    """Get a single patient by ID."""
    try:
        patient = patient_service.get_patient_by_id(patient_id)
        return APIResponse(
            success=True,
            message="Patient fetched successfully",
            data=patient,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_patient(patient: PatientCreate):
    """Register a new patient."""
    try:
        patient_data = patient.model_dump()
        created = patient_service.create_patient(patient_data)
        logger.info(f"Patient registered: {created.get('id')}")
        return APIResponse(
            success=True,
            message="Patient registered successfully",
            data=created,
        )
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{patient_id}")
async def update_patient(patient_id: str, patient: PatientCreate):
    """Update an existing patient."""
    try:
        patient_data = patient.model_dump()
        updated = patient_service.update_patient(patient_id, patient_data)
        return APIResponse(
            success=True,
            message="Patient updated successfully",
            data=updated,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient record."""
    try:
        deleted = patient_service.delete_patient(patient_id)
        return APIResponse(
            success=True,
            message="Patient deleted successfully",
            data=deleted,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error deleting patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    """Get a summary of a patient's consultation history."""
    try:
        summary = patient_service.get_patient_summary(patient_id)
        return APIResponse(
            success=True,
            message="Patient summary fetched successfully",
            data=summary,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching patient summary {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
