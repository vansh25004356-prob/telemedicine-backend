"""
Service layer for Telemed AI Backend.
"""

from app.services.ai_service import generate_ai_response, generate_summary, test_ai_connection
from app.services.patient_service import patient_service
from app.services.consultation_service import consultation_service
from app.services.summary_service import summary_service

