"""
Summary API router - handles consultation summary endpoints.

Generates AI-powered summaries of medical consultations.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.schemas.common import APIResponse
from app.services.summary_service import summary_service
from app.exceptions import NotFoundException, ValidationException

router = APIRouter(
    prefix="/summaries",
    tags=["Summaries"],
)


@router.get("/{consultation_id}")
async def get_summary(consultation_id: str):
    """Get the summary for a consultation."""
    try:
        summary = summary_service.get_summary(consultation_id)
        return APIResponse(
            success=True,
            message="Summary fetched successfully",
            data=summary,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching summary for {consultation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{consultation_id}/generate")
async def generate_summary(consultation_id: str):
    """Generate an AI summary for a consultation."""
    try:
        summary = await summary_service.generate_consultation_summary(consultation_id)
        logger.info(f"Summary generated for consultation {consultation_id}")
        return APIResponse(
            success=True,
            message="Summary generated successfully",
            data=summary,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error generating summary for {consultation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
