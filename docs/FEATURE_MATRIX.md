# Javo Agents — Feature Truthfulness Matrix

**Updated:** 2026-11-12

| Feature | Status | Execution Mode in Dev/CI | Notes |
| :--- | :--- | :--- | :--- |
| Local FastAPI Runtime (`127.0.0.1:8000`) | Live Ready | Real SQLite + FastAPI | Serves both `/` and `/api` prefixes cleanly. |
| 8GB RAM Capability Benchmark (`GET /health/benchmark`, `scripts/benchmark_8gb.py`) | Live Ready | Real OS/CPU/RAM/Disk probe | Tested on Windows 10 `7.82 GB` host -> recommends `8gb_cpu_optimized` & `qwen2.5:3b`. |
| Free-First AI Provider Center (`$0` default budget) | Live Ready | Deterministic Fallback / Live when Ollama or Gemini Key configured | Supports custom OpenAI-compatible endpoints, provider testing, key deletion, quota tracking, and offline queue drain. |
| Master Orchestrator & 29 Specialist Agents | Live Ready (Local Heuristic + LLM) | Real Agent Dispatch + DB Execution History | Partial-approval pause & retry/recovery tested; LLM quality scales up when Ollama/Gemini is connected. |
| Goal Persistence ("1M views in 30 days on $0 budget") | Live Ready | SQLite-backed Milestones & Metric Evaluation | Survives runtime restarts; includes honest non-guarantee disclaimer and growth experiment suggestions. |
| Content Factory Local Folder Pipeline | Live Ready | Real Filesystem Scan + FFmpeg Probing | Probes media, drafts captions/hashtags, checks quality, and creates approval-gated pending schedules. |
| Facebook / Instagram / YouTube Publishing | Scaffold / Mock Mode | `MockConnector` (`mode="mock"`) | Real Graph/YouTube connectors implemented; live publishing awaits user OAuth credentials. |
| Smart Memory (Inspect / Edit / Export / Delete) | Live Ready | Real SQLite (`MemoryEntry`, `Preference`) | Exports redact PII and secret tokens via `PrivacyFirewall`. |
| Jarvis Voice Mode (Hinglish + Confirmation + Context) | Partially Live | Real Intent/Context/WAV Chime; Optional `piper`/`whisper-cli` | Multi-turn session state & sensitive confirmation gate verified; STT/TTS binaries degrade honestly when absent. |
| Telegram Remote Control | Simulated Webhook Ready | Mocked Bot Webhook + `PrivacyFirewall` Redaction | Fail-closed allowlist & `/stop` emergency stop verified; live Bot API requires user token. |
| Self-Upgrading Skill Sandbox & Rollback | Live Ready | Real AST + Isolated Subprocess (`python -I`) | Blocks forbidden imports/calls (`subprocess`, `eval`), scores trust, enforces upgrade approval, and rolls back via `.backup_*`. |
| Encrypted Backups (`.jbackup`) | Live Ready | Real PBKDF2 + Fernet Encryption | Verified create, list, integrity check, and path-safe restore. |
| Official Website (`apps/website`) | Live Ready | Next.js 15 Static Export (24 pages) | `$0/month` positioning, accessible dark/light themes, accurate `NavigatorJagdish/javo-agents` links. |
| Windows Desktop App (`apps/windows`) | Unsigned Installer Ready | Electron TypeScript + NSIS/Portable | Compiles cleanly; signing requires Authenticode certificate. |
| Android Companion (`apps/android`) | CI Validated Source | Jetpack Compose + Room + Tink Keystore | Verified via GitHub Actions Android CI; Play Store upload requires signing keystore. |
