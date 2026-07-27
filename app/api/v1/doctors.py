"""
Doctor API router - handles all doctor-related endpoints.

Provides:
- GET  /doctors - List all doctors
- GET  /doctors/available - List available doctors
- GET  /doctors/{doctor_id} - Get doctor profile
- PUT  /doctors/{doctor_id} - Update doctor profile
- GET  /doctors/{doctor_id}/stats - Get doctor statistics
- GET  /doctors/{doctor_id}/consultations - Get doctor consultations
- GET  /doctors/{doctor_id}/notes - Get doctor notes
- POST /doctors/{doctor_id}/notes - Create doctor note
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.schemas.common import APIResponse
from app.schemas.doctor import DoctorUpdate, DoctorNoteCreate
from app.services.doctor_service import doctor_service
from app.core.security import get_current_user, get_current_doctor
from app.exceptions import NotFoundException, ValidationException

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"],
)


@router.get("/")
async def get_doctors(
    available: bool = Query(False, description="Filter by available doctors"),
):
    """
    Get all doctors, optionally filtered by availability.

    - **available**: If true, only returns doctors currently available
    """
    try:
        if available:
            doctors = doctor_service.get_available_doctors()
            message = f"Found {len(doctors)} available doctors"
        else:
            doctors = doctor_service.get_all()
            message = "Doctors fetched successfully"

        return APIResponse(success=True, message=message, data=doctors)
    except Exception as e:
        logger.error(f"Error fetching doctors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def get_available_doctors():
    """Get all currently available doctors."""
    try:
        doctors = doctor_service.get_available_doctors()
        return APIResponse(
            success=True,
            message=f"Found {len(doctors)} available doctors",
            data=doctors,
        )
    except Exception as e:
        logger.error(f"Error fetching available doctors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the current authenticated doctor's profile.

    Requires doctor role.
    """
    try:
        doctor = doctor_service.get_profile_by_auth_id(current_user["id"])
        return APIResponse(
            success=True,
            message="Doctor profile fetched successfully",
            data=doctor,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching doctor profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}")
async def get_doctor(doctor_id: str):
    """Get a single doctor's profile by ID."""
    try:
        doctor = doctor_service.get_profile(doctor_id)
        return APIResponse(
            success=True,
            message="Doctor fetched successfully",
            data=doctor,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{doctor_id}")
async def update_doctor(
    doctor_id: str,
    data: DoctorUpdate,
    current_user: dict = Depends(get_current_doctor),
):
    """
    Update a doctor's profile.

    Requires doctor role. Doctors can only update their own profile.
    """
    try:
        # Verify the doctor owns this profile
        doctor = doctor_service.get_profile(doctor_id)
        if doctor.get("auth_user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Cannot update another doctor's profile")

        doctor_data = data.model_dump(exclude_unset=True)
        updated = doctor_service.update_profile(doctor_id, doctor_data)
        return APIResponse(
            success=True,
            message="Doctor profile updated successfully",
            data=updated,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}/stats")
async def get_doctor_stats(doctor_id: str):
    """Get comprehensive statistics for a doctor."""
    try:
        stats = doctor_service.get_stats(doctor_id)
        return APIResponse(
            success=True,
            message="Doctor stats fetched successfully",
            data=stats,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching doctor stats for {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}/consultations")
async def get_doctor_consultations(
    doctor_id: str,
    status: str = Query(None, description="Filter by status (active/completed)"),
):
    """Get consultations assigned to a doctor."""
    try:
        consultations = doctor_service.get_consultations(doctor_id, status)
        return APIResponse(
            success=True,
            message="Consultations fetched successfully",
            data=consultations,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching doctor consultations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}/notes")
async def get_doctor_notes(
    doctor_id: str,
    consultation_id: str = Query(None, description="Filter by consultation ID"),
):
    """Get notes created by a doctor."""
    try:
        notes = doctor_service.get_notes(doctor_id, consultation_id)
        return APIResponse(
            success=True,
            message="Notes fetched successfully",
            data=notes,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching doctor notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{doctor_id}/notes")
async def create_doctor_note(
    doctor_id: str,
    data: DoctorNoteCreate,
    current_user: dict = Depends(get_current_doctor),
):
    """
    Create a doctor note for a consultation.

    Requires doctor role.
    """
    try:
        note = doctor_service.create_note(
            doctor_id=doctor_id,
            consultation_id=data.consultation_id,
            notes=data.notes,
            is_private=data.is_private,
        )
        logger.info(f"Doctor note created for consultation {data.consultation_id}")
        return APIResponse(
            success=True,
            message="Note created successfully",
            data=note,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating doctor note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

