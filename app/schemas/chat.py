from pydantic import BaseModel


class StartConsultationRequest(BaseModel):
    patient_id: str


class StartConsultationResponse(BaseModel):
    consultation_id: str


class ChatMessageRequest(BaseModel):
    consultation_id: str
    message: str


class ChatMessageResponse(BaseModel):
    reply: str


class EndConsultationRequest(BaseModel):
    consultation_id: str