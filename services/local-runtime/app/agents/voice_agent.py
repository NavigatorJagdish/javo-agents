"""Voice Agent — processes voice commands, intent parsing, and TTS preparation."""

import logging
import re
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class VoiceAgent(BaseAgent):
    """Specialist agent for voice command parsing, transcription cleanup, and TTS output."""

    name = "voice_agent"
    display_name = "Voice Assistant"
    description = "Parses spoken user commands into structured intents, cleans transcriptions, and prepares Piper/local TTS payloads."
    version = "1.0.0"
    capabilities = ["voice_command", "tts_generation", "intent_parsing", "transcription_cleanup"]
    required_permissions = ["use_voice", "use_ai"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "transcript": {"type": "string"},
            "text": {"type": "string"},
            "voice_model": {"type": "string"},
            "language": {"type": "string"},
        },
    }
    output_schema = {"required": ["status"]}

    INTENT_PATTERNS = [
        (r"\b(stop|halt|emergency)\b", "emergency_stop"),
        (r"\b(pause|hold)\b", "pause_schedules"),
        (r"\b(resume|continue|start)\b", "resume_schedules"),
        (r"\b(publish|post|upload)\b", "publish_content"),
        (r"\b(report|analytics|metrics|stats)\b", "weekly_report"),
        (r"\b(status|health)\b", "system_status"),
    ]

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "parse_command")
        if action == "tts":
            return self._prepare_tts(task_data)
        return await self._parse_command(task_data)

    async def _parse_command(self, task_data: dict) -> dict:
        transcript = task_data.get("transcript", "").strip()
        if not transcript:
            return {"status": "error", "error": "Empty voice transcript"}

        lower = transcript.lower()
        detected_intent = "general_query"
        for pattern, intent in self.INTENT_PATTERNS:
            if re.search(pattern, lower):
                detected_intent = intent
                break

        spoken_reply = f"Understood. Executing {detected_intent.replace('_', ' ')}."
        tokens = 0
        if detected_intent == "general_query":
            spoken_reply, tokens = await self.ask_ai(
                self.ai_router,
                f"Reply concisely as a voice assistant to: {transcript}",
                fallback="I have logged your request and routed it to the assistant queue.",
            )

        return {
            "status": "success",
            "transcript": transcript,
            "intent": detected_intent,
            "spoken_reply": spoken_reply,
            "tokens_used": tokens,
        }

    def _prepare_tts(self, task_data: dict) -> dict:
        text = task_data.get("text", "").strip()
        if not text:
            return {"status": "error", "error": "Text is required for TTS"}
        voice_model = task_data.get("voice_model", "en_US-lessac-medium")
        language = task_data.get("language", "en")
        estimated_duration_s = round(max(1.0, len(text.split()) / 2.5), 1)
        payload: dict[str, Any] = {
            "engine": "piper_local",
            "voice_model": voice_model,
            "language": language,
            "text": text,
            "sample_rate": 22050,
            "estimated_duration_seconds": estimated_duration_s,
        }
        return {"status": "success", "tts_job": payload}
