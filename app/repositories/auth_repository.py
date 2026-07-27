"""
Auth repository - handles all authentication and user database operations.

Provides data access for:
- User registration and profile management
- Session management
- Password reset tokens
- Role management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from loguru import logger
from supabase import Client

from app.core.database import supabase
from app.exceptions import NotFoundException, ConflictException


class AuthRepository:
    """Repository for authentication and user-related database operations."""

    def __init__(self, client: Client = None):
        self.client = client or supabase

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Find a user by email in the Supabase auth.users or custom users table."""
        try:
            # Try Supabase admin API to get user by email
            response = self.client.auth.admin.get_user_by_email(email)
            if response and hasattr(response, 'user'):
                user = response.user
                return {
                    "id": user.id,
                    "email": user.email,
                    "email_verified": user.email_confirmed_at is not None,
                    "created_at": user.created_at,
                    "user_metadata": user.user_metadata or {},
                    "app_metadata": user.app_metadata or {},
                }
            return None
        except Exception as e:
            logger.debug(f"Supabase admin get_user_by_email failed: {str(e)}")
            # Fallback: check a profiles table if it exists
            try:
                response = (
                    self.client.table("user_profiles")
                    .select("*")
                    .eq("email", email)
                    .maybe_single()
                    .execute()
                )
                return response.data
            except Exception:
                return None

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Find a user by ID."""
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            if response and hasattr(response, 'user'):
                user = response.user
                return {
                    "id": user.id,
                    "email": user.email,
                    "email_verified": user.email_confirmed_at is not None,
                    "created_at": user.created_at,
                    "user_metadata": user.user_metadata or {},
                    "app_metadata": user.app_metadata or {},
                }
            return None
        except Exception as e:
            logger.debug(f"Supabase admin get_user_by_id failed: {str(e)}")
            return None

    def create_user(self, email: str, password: str, user_data: dict) -> dict:
        """
        Create a new user via Supabase Auth admin API.
        Falls back to the signup endpoint if admin API is unavailable.
        """
        try:
            # Try admin API first
            response = self.client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "name": user_data.get("name", ""),
                    "role": user_data.get("role", "patient"),
                },
                "app_metadata": {
                    "role": user_data.get("role", "patient"),
                },
            })
            if response and hasattr(response, 'user'):
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {},
                    "app_metadata": response.user.app_metadata or {},
                }
        except Exception as e:
            logger.warning(f"Admin create_user failed, falling back to signup: {str(e)}")

        # Fallback: use signup
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": user_data.get("name", ""),
                        "role": user_data.get("role", "patient"),
                    },
                },
            })
            if response and hasattr(response, 'user') and response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {},
                    "app_metadata": response.user.app_metadata or {},
                }
            raise Exception("Failed to create user via signup")
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate a user with email and password via Supabase."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            if response and hasattr(response, 'user') and response.user:
                session = response.session
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "access_token": session.access_token if session else None,
                    "refresh_token": session.refresh_token if session else None,
                    "expires_in": session.expires_in if session else 3600,
                    "user_metadata": response.user.user_metadata or {},
                    "app_metadata": response.user.app_metadata or {},
                }
            return None
        except Exception as e:
            logger.warning(f"Authentication failed for {email}: {str(e)}")
            return None

    def sign_out(self, access_token: str) -> bool:
        """Sign out a user by invalidating their session."""
        try:
            self.client.auth.admin.sign_out(access_token)
            return True
        except Exception as e:
            logger.warning(f"Sign out failed: {str(e)}")
            # Fallback: local signout
            try:
                self.client.auth.sign_out()
                return True
            except Exception:
                return False

    def send_password_reset_email(self, email: str) -> bool:
        """Send a password reset email to the user."""
        try:
            self.client.auth.reset_password_email(email)
            logger.info(f"Password reset email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using a reset token."""
        try:
            self.client.auth.verify_and_reset_password(token, new_password)
            logger.info("Password reset successful")
            return True
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise

    def update_user_metadata(self, user_id: str, metadata: dict) -> Optional[dict]:
        """Update user metadata (name, role, etc.)."""
        try:
            response = self.client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": metadata},
            )
            if response and hasattr(response, 'user'):
                return {
                    "id": response.user.id,
                    "user_metadata": response.user.user_metadata or {},
                }
            return None
        except Exception as e:
            logger.error(f"Failed to update user metadata: {str(e)}")
            return None

    def create_password_reset_token(self, user_id: str) -> str:
        """Create a password reset token and store it."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        try:
            self.client.table("password_reset_tokens").insert({
                "user_id": user_id,
                "token": token,
                "expires_at": expires_at.isoformat(),
                "used": False,
            }).execute()
            return token
        except Exception as e:
            logger.error(f"Failed to create reset token: {str(e)}")
            raise

    def validate_reset_token(self, token: str) -> Optional[dict]:
        """Validate a password reset token."""
        try:
            response = (
                self.client.table("password_reset_tokens")
                .select("*")
                .eq("token", token)
                .eq("used", False)
                .gte("expires_at", datetime.now(timezone.utc).isoformat())
                .maybe_single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to validate reset token: {str(e)}")
            return None

    def mark_token_used(self, token_id: str) -> bool:
        """Mark a password reset token as used."""
        try:
            self.client.table("password_reset_tokens").update({
                "used": True,
            }).eq("id", token_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark token as used: {str(e)}")
            return False

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile from custom user_profiles table."""
        try:
            response = (
                self.client.table("user_profiles")
                .select("*")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            return response.data
        except Exception:
            return None

    def upsert_user_profile(self, user_id: str, profile_data: dict) -> dict:
        """Create or update a user profile."""
        try:
            data = {"id": user_id, **profile_data, "updated_at": datetime.now(timezone.utc).isoformat()}
            response = (
                self.client.table("user_profiles")
                .upsert(data)
                .execute()
            )
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Failed to upsert user profile: {str(e)}")
            raise


# Singleton instance
auth_repository = AuthRepository()

