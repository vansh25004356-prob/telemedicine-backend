"""
Schema definitions for Telemed AI Backend.
"""

from app.schemas.chat import (
    StartConsultationRequest,
    StartConsultationResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    EndConsultationRequest,
)
from app.schemas.patient import PatientCreate
from app.schemas.auth import (
    TokenResponse,
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    DoctorCreateRequest,
    ChangePasswordRequest,
)
from app.schemas.doctor import (
    DoctorBase,
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    DoctorNoteCreate,
    DoctorNoteUpdate,
)
from app.schemas.common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    HealthResponse,
    VersionResponse,
)

