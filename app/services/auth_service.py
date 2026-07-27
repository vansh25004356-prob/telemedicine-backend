"""
Auth service - business logic for authentication and user management.

Handles:
- User registration with Supabase Auth
- Email/password login
- Password reset flow
- Token management
- Role-based access control
- Profile management
"""

from typing import Optional

from loguru import logger

from app.repositories.auth_repository import auth_repository
from app.repositories.patient_repository import patient_repository
from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.exceptions import (
    ValidationException,
    UnauthorizedException,
    ConflictException,
    NotFoundException,
)


class AuthService:
    """Service layer for authentication and authorization operations."""

    def register(self, email: str, password: str, name: str, role: str = "patient") -> dict:
        """
        Register a new user and create their profile.
        
        Steps:
        1. Create user in Supabase Auth
        2. Create user profile record
        3. For patients, create a patient record
        4. For doctors, create a doctor profile record
        5. Return JWT token
        """
        # Validate role
        if role not in ("patient", "doctor"):
            raise ValidationException("Role must be 'patient' or 'doctor'")

        # Validate password strength
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters")

        try:
            # Create user in Supabase Auth
            user = auth_repository.create_user(email, password, {
                "name": name,
                "role": role,
            })

            user_id = user["id"]

            # Create user profile
            auth_repository.upsert_user_profile(user_id, {
                "email": email,
                "name": name,
                "role": role,
            })

            # Create role-specific profile
            if role == "patient":
                patient_repository.create({
                    "auth_user_id": user_id,
                    "name": name,
                    "age": 0,
                    "gender": "other",
                    "phone": "",
                })
                logger.info(f"Patient profile created for user {user_id}")
            elif role == "doctor":
                # Doctor profile creation will be handled separately
                logger.info(f"Doctor user {user_id} registered, profile setup pending")

            # Generate token
            token = create_access_token(
                data={"sub": user_id, "role": role, "email": email},
            )

            logger.info(f"User registered successfully: {email} as {role}")

            return {
                "success": True,
                "message": "Registration successful",
                "token": token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "role": role,
                },
            }

        except ConflictException:
            raise
        except Exception as e:
            logger.error(f"Registration failed for {email}: {str(e)}")
            raise

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a user with email and password.
        
        Returns JWT token and user profile on success.
        """
        try:
            # Authenticate with Supabase
            auth_result = auth_repository.authenticate_user(email, password)

            if not auth_result:
                raise UnauthorizedException("Invalid email or password")

            user_id = auth_result["id"]
            user_metadata = auth_result.get("user_metadata", {})
            app_metadata = auth_result.get("app_metadata", {})

            # Determine role from metadata
            role = app_metadata.get("role") or user_metadata.get("role", "patient")

            # Generate custom JWT for API authorization
            token = create_access_token(
                data={"sub": user_id, "role": role, "email": email},
            )

            logger.info(f"User logged in: {email} ({role})")

            return {
                "success": True,
                "message": "Login successful",
                "token": token,
                "refresh_token": auth_result.get("refresh_token"),
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": user_metadata.get("name", ""),
                    "role": role,
                },
            }

        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Login failed for {email}: {str(e)}")
            raise UnauthorizedException("Invalid email or password")

    def logout(self, access_token: str) -> dict:
        """Log out a user by invalidating their session."""
        try:
            auth_repository.sign_out(access_token)
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return {"success": False, "message": "Logout failed"}

    def get_profile(self, user_id: str) -> dict:
        """Get user profile by user ID."""
        try:
            user = auth_repository.get_user_by_id(user_id)
            if not user:
                raise NotFoundException("User", user_id)

            profile = auth_repository.get_user_profile(user_id)
            user_metadata = user.get("user_metadata", {})

            return {
                "id": user_id,
                "email": user.get("email", ""),
                "name": profile.get("name") if profile else user_metadata.get("name", ""),
                "role": profile.get("role") if profile else user_metadata.get("role", "patient"),
                "created_at": user.get("created_at"),
                "email_verified": user.get("email_verified", False),
            }

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get profile for {user_id}: {str(e)}")
            raise

    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> dict:
        """Change user password."""
        if len(new_password) < 8:
            raise ValidationException("New password must be at least 8 characters")

        try:
            # Update password via Supabase
            self.client.auth.admin.update_user_by_id(user_id, {
                "password": new_password,
            })

            logger.info(f"Password changed for user {user_id}")
            return {"success": True, "message": "Password changed successfully"}

        except Exception as e:
            logger.error(f"Failed to change password: {str(e)}")
            raise

    def forgot_password(self, email: str) -> dict:
        """Send password reset email."""
        try:
            sent = auth_repository.send_password_reset_email(email)
            if not sent:
                logger.warning(f"Failed to send password reset email to {email}")

            # Always return success to prevent email enumeration
            return {
                "success": True,
                "message": "If the email exists, a password reset link has been sent.",
            }

        except Exception as e:
            logger.error(f"Forgot password failed for {email}: {str(e)}")
            return {
                "success": True,
                "message": "If the email exists, a password reset link has been sent.",
            }

    def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password using a valid reset token."""
        if len(new_password) < 8:
            raise ValidationException("Password must be at least 8 characters")

        try:
            # Validate token
            token_data = auth_repository.validate_reset_token(token)
            if not token_data:
                raise ValidationException("Invalid or expired reset token")

            # Reset password
            auth_repository.reset_password(token, new_password)

            # Mark token as used
            auth_repository.mark_token_used(token_data["id"])

            logger.info("Password reset completed successfully")
            return {"success": True, "message": "Password reset successfully"}

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise

    def refresh_token(self, refresh_token: str) -> dict:
        """Refresh an access token using a refresh token."""
        try:
            response = auth_repository.client.auth.refresh_session(refresh_token)
            if response and hasattr(response, 'session'):
                session = response.session
                user = response.user
                user_metadata = user.user_metadata or {}
                app_metadata = user.app_metadata or {}
                role = app_metadata.get("role") or user_metadata.get("role", "patient")

                token = create_access_token(
                    data={"sub": user.id, "role": role, "email": user.email},
                )

                return {
                    "success": True,
                    "token": token,
                    "refresh_token": session.refresh_token,
                    "expires_in": session.expires_in,
                }

            raise UnauthorizedException("Invalid refresh token")

        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise UnauthorizedException("Invalid refresh token")


# Singleton instance
auth_service = AuthService()

