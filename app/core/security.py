"""
Security utilities for Telemed AI Backend.

Handles:
- JWT token creation and validation
- Password hashing and verification
- Authentication dependencies for FastAPI
- Role-based access control
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Dependency to get the current authenticated user.
    Works with both Supabase Auth tokens and custom JWT tokens.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try custom JWT first
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "patient")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return {"id": user_id, "role": role, "auth_provider": "jwt"}
    except HTTPException:
        raise
    except Exception:
        # If custom JWT fails, could try Supabase Auth
        # For now, raise unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def get_current_doctor(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency to ensure the current user is a doctor."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor role required.",
        )
    return current_user


async def get_current_patient(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency to ensure the current user is a patient."""
    if current_user.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient role required.",
        )
    return current_user


def create_doctor_token(doctor_id: str) -> str:
    """Create a JWT token for a doctor."""
    return create_access_token(
        data={"sub": doctor_id, "role": "doctor"},
    )


def create_patient_token(patient_id: str) -> str:
    """Create a JWT token for a patient."""
    return create_access_token(
        data={"sub": patient_id, "role": "patient"},
    )

