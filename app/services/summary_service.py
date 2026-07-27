"""
Summary service - business logic for generating consultation summaries.
"""

from loguru import logger

from app.repositories.summary_repository import summary_repository
from app.repositories.chat_repository import chat_repository
from app.repositories.consultation_repository import consultation_repository
from app.services.ai_service import generate_summary
from app.exceptions import ValidationException


class SummaryService:
    """Service layer for consultation summary operations."""

    async def generate_consultation_summary(self, consultation_id: str) -> dict:
        """Generate an AI summary for a consultation."""
        # Verify consultation exists
        consultation = consultation_repository.get_by_id(consultation_id)

        # Get conversation history
        messages = chat_repository.get_messages(consultation_id)
        if not messages:
            raise ValidationException("No messages to summarize")

        # Generate summary using AI
        conversation_text = self._format_conversation(messages)
        summary_text = await generate_summary(conversation_text)

        # Check if summary already exists
        if summary_repository.exists(consultation_id):
            summary_data = summary_repository.update(consultation_id, {
                "summary_text": summary_text,
                "status": "completed",
            })
        else:
            summary_data = summary_repository.create(consultation_id, {
                "summary_text": summary_text,
                "status": "completed",
            })

        logger.info(f"Generated summary for consultation {consultation_id}")
        return summary_data

    def get_summary(self, consultation_id: str) -> dict:
        """Get the summary for a consultation."""
        return summary_repository.get_by_consultation_id(consultation_id)

    def _format_conversation(self, messages: list) -> str:
        """Format chat messages into a conversation text for the AI."""
        formatted = []
        for msg in messages:
            sender = "Patient" if msg.get("sender") == "user" else "Doctor"
            formatted.append(f"{sender}: {msg.get('message', '')}")
        return "\n".join(formatted)


# Singleton instance
summary_service = SummaryService()
