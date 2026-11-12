# Privacy Guide

Javo Agents is built on a **Local-First Privacy Architecture**.

## 1. Where Your Data Lives

- **SQLite Database & Logs**: Stored exclusively on your Windows PC. There is no Javo telemetry server or cloud database.
- **Voice Audio & Transcripts**: Processed locally via `whisper.cpp` (STT) and `Piper` (TTS). Raw microphone audio never leaves your machine.
- **Drafts & Media**: Stay in your chosen local `content_root` folder until you approve a post for publishing.

## 2. Strict Local Privacy Mode

Enable **Strict Local Mode** (`localPrivacyMode: true`) in **Settings → Privacy**:
- All LLM prompts run through local **Ollama** models.
- Outbound calls to Gemini or OpenAI-compatible APIs are blocked by the Privacy Firewall (`privacy_firewall.py`).
- Ideal for unreleased videos, client NDAs, and sensitive creator analytics.

## 3. Opt-In Cloud Services

If you choose to enable optional cloud integrations:
- **Gemini API**: Only the specific prompt text you send is transmitted to Google's Generative Language API. See [GEMINI_SETUP.md](../setup/GEMINI_SETUP.md) for free-tier vs paid-tier data handling notices.
- **Telegram Bot**: Only notifications, approval prompts, and commands sent by your allowlisted Telegram user ID travel through Telegram's Bot API.
- **Social APIs**: Only approved media, captions, and read-only analytics requests are exchanged with YouTube, Instagram, or Facebook.
