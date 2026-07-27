"""
AI Service for Telemed AI Backend.

Handles all interactions with OpenRouter/LLM APIs.
Provides:
- Medical intake conversation
- Emergency detection
- Summary generation
- Structured outputs
- Hallucination reduction
"""

import json
import re
from datetime import datetime
from typing import Optional

from loguru import logger
from openai import OpenAI

from app.core.config import settings

# ── OpenAI Client ──────────────────────────────────────────
client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


# ── System Prompts ─────────────────────────────────────────

MEDICAL_INTAKE_PROMPT = """You are an AI Medical Intake Assistant for Telemed AI Platform.

YOUR ROLE:
- Collect patient medical information systematically.
- Ask ONE question at a time.
- Be empathetic, professional, and concise.
- Use simple language that is easy to understand.

INFORMATION TO COLLECT:
1. Chief complaint (main reason for visit)
2. Symptoms (detailed description)
3. Duration (when did it start?)
4. Severity (mild, moderate, severe)
5. Allergies (medication, food, environmental)
6. Current medications
7. Existing medical conditions
8. Vital signs if available (temperature, blood pressure, etc.)

CRITICAL RULES:
- NEVER diagnose diseases or conditions.
- NEVER prescribe medications or treatments.
- NEVER recommend specific medical procedures.
- If a patient reports emergency symptoms (chest pain, difficulty breathing, severe bleeding, loss of consciousness, suicidal thoughts), immediately respond with: EMERGENCY_ALERT: [description] and advise them to call emergency services.
- Ask only ONE question at a time.
- Keep responses under 150 words.
- Be respectful and culturally sensitive.

CONSULTATION COMPLETION:
When you have collected sufficient information (at minimum: chief complaint, symptoms, duration, and severity), respond with:

END_CONSULTATION

Then provide a structured summary in this exact JSON format:
```json
{
    "chief_complaint": "Patient's main complaint",
    "symptoms": ["symptom1", "symptom2"],
    "duration": "duration description",
    "severity": "mild/moderate/severe",
    "allergies": ["allergy1"] or "none reported",
    "current_medications": ["med1"] or "none reported",
    "existing_conditions": ["condition1"] or "none reported",
    "vital_signs": {},
    "recommendation": "General health advice (not medical treatment)"
}
```

Remember: You are a medical INTAKE assistant, not a doctor. Your goal is to collect information for the doctor to review."""

SUMMARY_PROMPT = """You are a medical summarization AI. Your task is to analyze a doctor-patient conversation and produce a clear, structured summary.

Summarize the following medical consultation conversation. Include:
1. Chief Complaint
2. Symptoms Reported
3. Duration of Symptoms
4. Severity Assessment
5. Allergies
6. Current Medications
7. Existing Conditions
8. Key Recommendations

Format the summary in clear markdown with sections.

Conversation:
{conversation_text}

Generate the summary now."""


# ── Emergency Keywords ─────────────────────────────────────
EMERGENCY_KEYWORDS = [
    "chest pain", "difficulty breathing", "shortness of breath",
    "severe bleeding", "unconscious", "loss of consciousness",
    "not breathing", "heart attack", "stroke", "seizure",
    "suicidal", "overdose", "severe allergic reaction",
    "anaphylaxis", "head injury", "broken bone",
    "severe burn", "poisoning", "choking",
]


def detect_emergency(message: str) -> Optional[str]:
    """
    Detect if a message contains emergency keywords.
    Returns the matched emergency keyword if found, None otherwise.
    """
    message_lower = message.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in message_lower:
            return keyword
    return None


def build_system_prompt(patient_info: Optional[dict] = None) -> str:
    """
    Build the system prompt with optional patient context.
    """
    prompt = MEDICAL_INTAKE_PROMPT

    if patient_info:
        patient_context = f"""
PATIENT CONTEXT:
- Name: {patient_info.get('name', 'Unknown')}
- Age: {patient_info.get('age', 'Unknown')}
- Gender: {patient_info.get('gender', 'Unknown')}
"""
        prompt += patient_context

    prompt += f"""
Current date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
    return prompt


async def generate_ai_response(
    messages: list,
    patient_info: dict | None = None,
) -> str:

    # Emergency detection
    if messages and messages[-1]["role"] == "user":
        emergency = detect_emergency(messages[-1]["content"])
        if emergency:
            return (
                f"🚨 EMERGENCY ALERT\n\n"
                f"I detected possible {emergency}. "
                f"Please call your local emergency services immediately."
            )

    system_prompt = build_system_prompt(patient_info)

    try:

        print("=" * 80)
        print("History length:", len(messages))
        print(messages)
        print("=" * 80)

        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
        )

        logger.debug(f"OpenRouter Response:\n{response}")

        print("=" * 80)
        print(response)
        print("=" * 80)

        if not response.choices:
            raise Exception("No choices returned from OpenRouter.")

        message = response.choices[0].message

        reply = message.content

        if not reply:
            reply = getattr(message, "reasoning", None)

        if not reply:
            raise Exception(f"Model returned no content.\n{response}")

        reply = reply.strip()

        logger.debug(f"AI response generated ({len(reply)} chars)")

        return reply
    except Exception as e:
        logger.exception(e)
        raise

async def generate_summary(conversation_text: str) -> str:
    """
    Generate a structured summary from a conversation.

    Args:
        conversation_text: The full conversation text.

    Returns:
        Markdown-formatted summary.
    """
    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SUMMARY_PROMPT.format(
                        conversation_text=conversation_text
                    ),
                },
            ],
            temperature=0.2,  # Lower temperature for more consistent summaries
            max_tokens=800,
        )

        summary = response.choices[0].message.content
        logger.info(f"Summary generated ({len(summary)} chars)")
        return summary

    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        raise


async def test_ai_connection() -> bool:
    """
    Test the AI service connection.
    Returns True if the API is reachable and responding.
    """
    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[
                {"role": "user", "content": "Reply with only the word: OK"}
            ],
            temperature=0.1,
            max_tokens=10,
        )
        message = response.choices[0].message
        reply = message.content or getattr(message, "reasoning", "")

        return "ok" in reply.lower()
    except Exception as e:
        logger.error(f"AI connection test failed: {str(e)}")
        return False
