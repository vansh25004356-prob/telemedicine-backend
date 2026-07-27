"""
Chat API router - handles all consultation chat endpoints.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.schemas.chat import (
    StartConsultationRequest,
    ChatMessageRequest,
    EndConsultationRequest,
)

from app.schemas.common import APIResponse

from app.services.consultation_service import consultation_service

from app.exceptions import (
    NotFoundException,
    ValidationException,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/test")
async def test_ai():
    """Test AI service."""

    try:
        from app.services.ai_service import test_ai_connection

        healthy = await test_ai_connection()

        return APIResponse(
            success=healthy,
            message="AI service is healthy"
            if healthy
            else "AI service unavailable",
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/start")
async def start_consultation(
    data: StartConsultationRequest,
):
    """Start consultation."""

    try:
        consultation = consultation_service.start_consultation(
            data.patient_id
        )

        return {
            "success": True,
            "consultation_id": consultation["id"],
        }

    except NotFoundException as e:
        raise HTTPException(
            status_code=404,
            detail=e.message,
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/message")
async def send_message(
    data: ChatMessageRequest,
):
    """Send message."""

    try:
        result = await consultation_service.send_message(
            data.consultation_id,
            data.message,
        )

        return {
            "success": True,
            "reply": result["reply"],
        }

    except NotFoundException as e:
        raise HTTPException(
            status_code=404,
            detail=e.message,
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=400,
            detail=e.message,
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/{consultation_id}")
async def get_chat(
    consultation_id: str,
):
    """Get consultation chat."""

    try:
        messages = consultation_service.get_consultation_history(
            consultation_id
        )

        return {
            "success": True,
            "messages": messages,
        }

    except NotFoundException as e:
        raise HTTPException(
            status_code=404,
            detail=e.message,
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/end")
async def end_consultation(
    data: EndConsultationRequest,
):
    """End consultation."""

    try:
        result = consultation_service.end_consultation(
            data.consultation_id
        )

        return {
            "success": True,
            "message": result["message"],
        }

    except NotFoundException as e:
        raise HTTPException(
            status_code=404,
            detail=e.message,
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=400,
            detail=e.message,
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )