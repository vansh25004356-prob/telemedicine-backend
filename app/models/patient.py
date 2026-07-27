"""
Patient model type definition.

Matches the 'patients' table in Supabase PostgreSQL.
"""

from datetime import datetime
from typing import Optional


class Patient:
    """
    Represents a patient record.

    Database table: patients
    """

    def __init__(
        self,
        id: str,
        name: str,
        age: int,
        gender: str,
        phone: Optional[str] = None,
        village: Optional[str] = None,
        address: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone
        self.village = village
        self.address = address
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "phone": self.phone,
            "village": self.village,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Patient":
        """Create a Patient instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            age=data.get("age", 0),
            gender=data.get("gender", ""),
            phone=data.get("phone"),
            village=data.get("village"),
            address=data.get("address"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
