"""
Authentication and authorization schemas.

Provides request/response models for:
- Email/password login and registration
- Password reset flow
- Profile management
- Token management
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Schema for user registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="patient", pattern="^(patient|doctor)$")


class AuthResponse(BaseModel):
    """Schema for authentication response."""
    success: bool
    message: str
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[dict] = None


class DoctorCreateRequest(BaseModel):
    """Schema for creating a doctor profile."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Schema for change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    id: str
    email: str
    name: str
    role: str
    created_at: Optional[datetime] = None
    email_verified: bool = False

    class Config:
        from_attributes = True

