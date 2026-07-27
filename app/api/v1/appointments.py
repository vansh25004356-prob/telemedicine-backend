"""
Appointment API router - handles all appointment endpoints.

Provides:
- GET    /appointments - List appointments
- POST   /appointments - Book appointment
- GET    /appointments/upcoming - Get upcoming appointments
- GET    /appointments/{id} - Get appointment details
- PUT    /appointments/{id} - Update appointment
- DELETE /appointments/{id} - Delete appointment
- POST   /appointments/{id}/cancel - Cancel appointment
- POST   /appointments/{id}/reschedule - Reschedule appointment
- POST   /appointments/{id}/confirm - Confirm appointment
- POST   /appointments/{id}/complete - Complete appointment
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from loguru import logger
from pydantic import BaseModel, Field

from app.schemas.common import APIResponse
from app.services.appointment_service import appointment_service
from app.core.security import get_current_user, get_current_doctor
from app.exceptions import NotFoundException, ValidationException


class BookAppointmentRequest(BaseModel):
    """Request schema for booking an appointment."""
    patient_id: str
    doctor_id: str
    scheduled_date: str = Field(..., description="ISO 8601 datetime string")
    reason: str = Field(..., min_length=3)
    notes: Optional[str] = None


class RescheduleRequest(BaseModel):
    """Request schema for rescheduling."""
    new_date: str = Field(..., description="New ISO 8601 datetime string")


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)


@router.get("/")
async def get_appointments(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
):
    """Get appointments, optionally filtered by status."""
    try:
        appointments = appointment_service.get_upcoming() if not status else None
        if appointments is None:
            # Fallback to all if no filter specified
            from app.repositories.appointment_repository import appointment_repository
            appointments = appointment_repository.get_all(status)

        return APIResponse(
            success=True,
            message="Appointments fetched successfully",
            data=appointments,
        )
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def get_upcoming_appointments(
    limit: int = Query(10, ge=1, le=50),
):
    """Get upcoming scheduled appointments."""
    try:
        appointments = appointment_service.get_upcoming(limit)
        return APIResponse(
            success=True,
            message=f"Found {len(appointments)} upcoming appointments",
            data=appointments,
        )
    except Exception as e:
        logger.error(f"Error fetching upcoming appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def book_appointment(
    data: BookAppointmentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Book a new appointment."""
    try:
        appointment = appointment_service.book_appointment(data.model_dump())
        logger.info(f"Appointment booked by user {current_user['id']}")
        return APIResponse(
            success=True,
            message="Appointment booked successfully",
            data=appointment,
        )
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{appointment_id}")
async def get_appointment(appointment_id: str):
    """Get appointment details."""
    try:
        appointment = appointment_service.get_appointment(appointment_id)
        return APIResponse(
            success=True,
            message="Appointment fetched successfully",
            data=appointment,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching appointment {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel an appointment."""
    try:
        result = appointment_service.cancel_appointment(appointment_id)
        logger.info(f"Appointment {appointment_id} cancelled by user {current_user['id']}")
        return APIResponse(success=True, message="Appointment cancelled", data=result)
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error cancelling appointment {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    data: RescheduleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Reschedule an appointment to a new date/time."""
    try:
        result = appointment_service.reschedule_appointment(appointment_id, data.new_date)
        logger.info(f"Appointment {appointment_id} rescheduled by user {current_user['id']}")
        return APIResponse(success=True, message="Appointment rescheduled", data=result)
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error rescheduling appointment {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_doctor),
):
    """Confirm a scheduled appointment (Doctor only)."""
    try:
        result = appointment_service.confirm_appointment(appointment_id)
        return APIResponse(success=True, message="Appointment confirmed", data=result)
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error confirming appointment {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_doctor),
):
    """Mark an appointment as completed (Doctor only)."""
    try:
        result = appointment_service.complete_appointment(appointment_id)
        return APIResponse(success=True, message="Appointment completed", data=result)
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error completing appointment {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

