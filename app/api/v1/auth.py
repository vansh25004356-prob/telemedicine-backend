"""
Auth API router - handles all authentication and user management endpoints.

Provides:
- POST /auth/register - User registration
- POST /auth/login - User login
- POST /auth/logout - User logout
- GET  /auth/me - Get current user profile
- PUT  /auth/change-password - Change password
- POST /auth/forgot-password - Request password reset
- POST /auth/reset-password - Reset password with token
- POST /auth/refresh - Refresh access token
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserProfileResponse,
)
from app.schemas.common import APIResponse
from app.services.auth_service import auth_service
from app.core.security import get_current_user, decode_access_token
from app.exceptions import (
    NotFoundException,
    ValidationException,
    UnauthorizedException,
    ConflictException,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest):
    """
    Register a new user.

    Creates a new user account via Supabase Auth and sets up
    the appropriate profile (patient or doctor).

    - **email**: User's email address
    - **password**: Password (min 8 characters)
    - **name**: Full name
    - **role**: 'patient' or 'doctor' (default: patient)
    """
    try:
        result = auth_service.register(
            email=data.email,
            password=data.password,
            name=data.name,
            role=data.role,
        )
        return AuthResponse(
            success=True,
            message=result["message"],
            token=result.get("token"),
            user=result.get("user"),
        )
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    """
    Authenticate a user with email and password.

    Returns a JWT access token and user profile on success.
    """
    try:
        result = auth_service.login(
            email=data.email,
            password=data.password,
        )
        return AuthResponse(
            success=True,
            message=result["message"],
            token=result.get("token"),
            refresh_token=result.get("refresh_token"),
            user=result.get("user"),
        )
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Log out the current user.

    Invalidates the current session token.
    Requires authentication.
    """
    try:
        result = auth_service.logout("")
        return APIResponse(success=result["success"], message=result["message"])
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.

    Returns user details including id, email, name, role.
    Requires authentication.
    """
    try:
        profile = auth_service.get_profile(current_user["id"])
        return APIResponse(
            success=True,
            message="Profile fetched successfully",
            data=profile,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Change the current user's password.

    Requires the current password for verification.
    """
    try:
        result = auth_service.change_password(
            user_id=current_user["id"],
            current_password=data.current_password,
            new_password=data.new_password,
        )
        return APIResponse(success=result["success"], message=result["message"])
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """
    Request a password reset email.

    If the email exists in the system, a password reset
    link will be sent. Always returns success to prevent
    email enumeration.
    """
    try:
        result = auth_service.forgot_password(email=data.email)
        return APIResponse(success=result["success"], message=result["message"])
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return APIResponse(
            success=True,
            message="If the email exists, a password reset link has been sent.",
        )


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """
    Reset password using a valid reset token.

    - **token**: The password reset token (received via email)
    - **new_password**: New password (min 8 characters)
    """
    try:
        result = auth_service.reset_password(
            token=data.token,
            new_password=data.new_password,
        )
        return APIResponse(success=result["success"], message=result["message"])
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh an expired access token using a refresh token.

    Returns a new access token and refresh token pair.
    """
    try:
        result = auth_service.refresh_token(data.refresh_token)
        return {
            "success": True,
            "token": result["token"],
            "refresh_token": result["refresh_token"],
            "expires_in": result["expires_in"],
        }
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

