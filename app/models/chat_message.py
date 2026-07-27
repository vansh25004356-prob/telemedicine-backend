"""
Chat message model type definition.

Matches the 'chat_messages' table in Supabase PostgreSQL.
"""

from datetime import datetime
from typing import Optional


class ChatMessage:
    """
    Represents a single chat message in a consultation.

    Database table: chat_messages
    """

    def __init__(
        self,
        id: str,
        consultation_id: str,
        sender: str,
        message: str,
        metadata: Optional[dict] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.consultation_id = consultation_id
        self.sender = sender
        self.message = message
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "consultation_id": self.consultation_id,
            "sender": self.sender,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
