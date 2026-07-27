"""
Doctor schemas for Telemed AI Backend.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class DoctorBase(BaseModel):
    """Base schema for doctor data."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    is_available: bool = True


class DoctorCreate(DoctorBase):
    """Schema for creating a doctor."""
    pass


class DoctorUpdate(BaseModel):
    """Schema for updating a doctor."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    is_available: Optional[bool] = None


class DoctorResponse(DoctorBase):
    """Schema for doctor response."""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoctorNoteCreate(BaseModel):
    """Schema for creating a doctor note."""
    consultation_id: str
    notes: str = Field(..., min_length=1)
    is_private: bool = False


class DoctorNoteUpdate(BaseModel):
    """Schema for updating a doctor note."""
    notes: Optional[str] = None
    is_private: Optional[bool] = None

