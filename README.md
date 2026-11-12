# Javo Agents

Local-first, privacy-preserving multi-agent automation platform for creators, social growth, and personal workflows.

## Architecture

- **Local Runtime (`services/local-runtime/`)**: Python FastAPI backend with SQLite async persistence, APScheduler job recovery, Privacy Firewall, multi-provider AI Router (Ollama / Gemini / OpenAI-compatible), and 29 specialized agents coordinated by `MasterAgent`.
- **Dashboard (`apps/dashboard/`)**: React + TypeScript + Tailwind CSS desktop dashboard with visual node-based workflow editor.
- **Desktop Shell (`apps/windows/`)**: Electron wrapper for Windows with system tray controls and emergency stop.
- **Mobile Companion (`apps/android/`)**: Android companion app with secure device pairing.

## Quick Start (Backend)

```bash
cd services/local-runtime
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Once running, open the interactive API docs at `http://localhost:8000/docs`.

## Key Features

- **29 Specialist Agents + Master Orchestrator**: Content creation, scheduling, growth analysis, compliance, security guarding, memory, and device sync.
- **Privacy Firewall**: Automatic PII/secret classification and egress blocking before any request reaches cloud AI providers.
- **Zero-Cost Local AI First**: Seamless Ollama integration with automatic fallback and budget guardrails for cloud APIs.
- **Encrypted Backups & Credential Vault**: Fernet symmetric encryption for tokens and `.jbackup` archives.
- **Persistent Scheduler**: APScheduler with SQLite job store and missed-job reconciliation on restart.

## Running Tests

```bash
cd services/local-runtime
pytest ../../tests
```

## License

MIT License — see [LICENSE](LICENSE).
