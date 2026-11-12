"""Voice command processing, TTS, and audio transcription routes."""

from __future__ import annotations

import base64
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.voice_service import (
    handle_voice_command,
    inspect_or_transcribe_audio,
    synthesize_wav,
)

router = APIRouter(prefix="/voice", tags=["voice"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class VoiceCommandRequest(BaseModel):
    transcript: Optional[str] = None
    text: Optional[str] = None
    language: str = "en"
    confirmed: bool = False
    session_id: str = "default"
    context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ensure_text_or_transcript(self) -> "VoiceCommandRequest":
        val = (self.transcript or self.text or "").strip()
        if not val:
            raise ValueError("Either 'transcript' or 'text' must be non-empty")
        self.transcript = val
        return self


class VoiceCommandResponse(BaseModel):
    intent: str
    response_text: str
    reply: str = ""
    routed_agent: str = "master_orchestrator"
    status: str = "completed"
    action_taken: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    context_turns: int = 1
    session_id: str = "default"
    data: dict[str, Any] = Field(default_factory=dict)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    language: str = "en"
    voice: str = "default"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class TTSResponse(BaseModel):
    mime_type: str
    audio_base64: str
    text_length: int
    engine: str


class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration_seconds: Optional[float] = None
    engine: str
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    body: VoiceCommandRequest,
    session: AsyncSession = Depends(get_session),
) -> VoiceCommandResponse:
    """Interpret and execute an English, Hindi, or Hinglish voice command with confirmation gating and context."""
    transcript = (body.transcript or body.text or "").strip()
    result = await handle_voice_command(
        session=session,
        transcript=transcript,
        session_id=body.session_id,
        language=body.language,
        confirmed=body.confirmed,
    )
    return VoiceCommandResponse(
        intent=result["intent"],
        response_text=result["response_text"],
        reply=result["reply"],
        routed_agent=result["routed_agent"],
        status=result["status"],
        action_taken=result.get("action_taken"),
        requires_confirmation=bool(result.get("requires_confirmation", False)),
        confirmation_prompt=result.get("confirmation_prompt"),
        context_turns=int(result.get("context_turns", 1)),
        session_id=result["session_id"],
        data={
            "language": body.language,
            "transcript": transcript,
            "context_turns": result.get("context_turns", 1),
        },
    )


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(body: TTSRequest) -> TTSResponse:
    """Synthesize speech WAV audio using local Piper TTS when installed or valid PCM audio fallback."""
    wav_bytes, engine = synthesize_wav(body.text)
    encoded = base64.b64encode(wav_bytes).decode("ascii")
    return TTSResponse(
        mime_type="audio/wav",
        audio_base64=encoded,
        text_length=len(body.text),
        engine=engine,
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(default="auto"),
) -> TranscribeResponse:
    """Validate audio and transcribe with local whisper.cpp CLI if installed."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded audio file is empty")

    res = inspect_or_transcribe_audio(data, language=language)
    return TranscribeResponse(
        text=str(res.get("text", "")),
        language=str(res.get("language", language)),
        duration_seconds=res.get("duration_seconds"),
        engine=str(res.get("engine", "audio_validated_no_stt_binary")),
        note=res.get("note"),
    )
