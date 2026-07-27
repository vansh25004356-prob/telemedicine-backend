"""
Chat repository - handles all chat message database operations.
"""

from loguru import logger

from app.core.database import supabase
from app.exceptions import NotFoundException


class ChatRepository:
    """Repository for chat message-related database operations."""

    def get_messages(self, consultation_id: str) -> list:
        """Fetch all messages for a consultation, ordered by creation time."""
        try:
            response = (
                supabase.table("chat_messages")
                .select("*")
                .eq("consultation_id", consultation_id)
                .order("created_at")
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(
                f"Error fetching messages for consultation {consultation_id}: {str(e)}"
            )
            raise

    def save_message(
        self,
        consultation_id: str,
        sender: str,
        message: str,
        metadata: dict = None,
    ) -> dict:
        """Save a chat message."""
        try:
            data = {
                "consultation_id": consultation_id,
                "sender": sender,
                "message": message,
            }
            if metadata:
                data["metadata"] = metadata

            response = (
                supabase.table("chat_messages")
                .insert(data)
                .execute()
            )
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise

    def save_user_message(self, consultation_id: str, message: str) -> dict:
        """Save a patient/user message."""
        return self.save_message(consultation_id, "user", message)

    def save_ai_message(self, consultation_id: str, message: str) -> dict:
        """Save an AI/assistant message."""
        return self.save_message(consultation_id, "assistant", message)

    def get_conversation_history(self, consultation_id: str) -> list[dict]:
        """
        Get conversation history formatted for the AI model.
        Returns list of {role, content} dicts.
        """
        messages = self.get_messages(consultation_id)
        formatted = []
        for msg in messages:
            role = "user" if msg["sender"] == "user" else "assistant"
            formatted.append({
                "role": role,
                "content": msg["message"],
            })
        return formatted

    def delete_messages(self, consultation_id: str) -> None:
        """Delete all messages for a consultation."""
        try:
            supabase.table("chat_messages").delete().eq(
                "consultation_id", consultation_id
            ).execute()
            logger.info(f"Deleted messages for consultation {consultation_id}")
        except Exception as e:
            logger.error(
                f"Error deleting messages for consultation {consultation_id}: {str(e)}"
            )
            raise


# Singleton instance
chat_repository = ChatRepository()

