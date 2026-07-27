"""
Consultation model type definition.

Matches the 'consultations' table in Supabase PostgreSQL.
"""

from datetime import datetime
from typing import Optional


class Consultation:
    """
    Represents a medical consultation session.

    Database table: consultations
    """

    def __init__(
        self,
        id: str,
        patient_id: str,
        doctor_id: Optional[str] = None,
        status: str = "active",
        symptoms: Optional[str] = None,
        diagnosis: Optional[str] = None,
        treatment: Optional[str] = None,
        notes: Optional[str] = None,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.status = status
        self.symptoms = symptoms
        self.diagnosis = diagnosis
        self.treatment = treatment
        self.notes = notes
        self.started_at = started_at or datetime.utcnow()
        self.ended_at = ended_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "status": self.status,
            "symptoms": self.symptoms,
            "diagnosis": self.diagnosis,
            "treatment": self.treatment,
            "notes": self.notes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
