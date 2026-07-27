"""
Consultation service - business logic for consultation operations.
"""

from loguru import logger

from app.repositories.consultation_repository import consultation_repository
from app.repositories.chat_repository import chat_repository
from app.repositories.patient_repository import patient_repository
from app.services.ai_service import generate_ai_response
from app.exceptions import ValidationException


class ConsultationService:
    """Service layer for consultation-related business logic."""

    def start_consultation(self, patient_id: str) -> dict:
        """Start a new consultation for a patient."""
        patient_repository.get_by_id(patient_id)

        consultation = consultation_repository.create(patient_id)

        logger.info(
            f"Started consultation {consultation.get('id')} for patient {patient_id}"
        )

        return consultation

    async def send_message(self, consultation_id: str, message: str) -> dict:
        """Process a chat message in a consultation."""

        consultation = consultation_repository.get_by_id(consultation_id)

        if consultation.get("status") != "active":
            raise ValidationException("Consultation is not active")

        # Save user message
        chat_repository.save_user_message(
            consultation_id,
            message,
        )

        # Get conversation history
        history = chat_repository.get_conversation_history(
            consultation_id
        )

        #Send only last 12 messages
        history = history[-12:]

        # Generate AI response
        ai_reply = await generate_ai_response(history)

        # Save AI response
        chat_repository.save_ai_message(
            consultation_id,
            ai_reply,
        )

        return {
            "reply": ai_reply,
            "consultation_id": consultation_id,
        }

    def end_consultation(self, consultation_id: str) -> dict:
        """End an active consultation."""

        consultation = consultation_repository.get_by_id(
            consultation_id
        )

        if consultation.get("status") != "active":
            raise ValidationException("Consultation is not active")

        consultation_repository.update_status(
            consultation_id,
            "completed",
        )

        logger.info(f"Ended consultation {consultation_id}")

        return {
            "message": "Consultation completed."
        }

    def get_consultation_history(self, consultation_id: str) -> list:
        """Get chat history."""
        return chat_repository.get_messages(
            consultation_id
        )

    def get_patient_consultations(self, patient_id: str) -> list:
        """Get all consultations for a patient."""
        return consultation_repository.get_by_patient_id(
            patient_id
        )

    def get_active_consultations(self) -> list:
        """Get active consultations."""
        return consultation_repository.get_active_consultations()

    def get_consultation_detail(self, consultation_id: str) -> dict:
        """Get consultation details."""

        consultation = consultation_repository.get_by_id(
            consultation_id
        )

        patient = patient_repository.get_by_id(
            consultation["patient_id"]
        )

        messages = chat_repository.get_messages(
            consultation_id
        )

        return {
            **consultation,
            "patient": patient,
            "messages": messages,
            "message_count": len(messages),
        }


consultation_service = ConsultationService()