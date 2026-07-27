"""
Doctor model type definition.

Matches the 'doctor_profiles' table in Supabase PostgreSQL.
"""

from datetime import datetime
from typing import Optional


class Doctor:
    """
    Represents a doctor profile.

    Database table: doctor_profiles
    """

    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        email: str,
        specialization: Optional[str] = None,
        license_number: Optional[str] = None,
        phone: Optional[str] = None,
        is_available: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.email = email
        self.specialization = specialization
        self.license_number = license_number
        self.phone = phone
        self.is_available = is_available
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "specialization": self.specialization,
            "license_number": self.license_number,
            "phone": self.phone,
            "is_available": self.is_available,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
