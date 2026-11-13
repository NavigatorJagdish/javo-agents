# Javo Agents

[![Open Javo Website](https://img.shields.io/badge/OPEN_JAVO_WEBSITE-00C8FF?style=for-the-badge&logo=googlechrome&logoColor=white)](https://javoagents.org)

**[🌐 Open Javo Website](https://javoagents.org)** · [🚀 Deploy / Repair Website](apps/website/DEPLOYMENT.md) · [View Website Source](https://github.com/NavigatorJagdish/javo-agents/tree/main/apps/website) · [Website Documentation](https://github.com/NavigatorJagdish/javo-agents/tree/main/docs)

> **Website deployment pending:** `javoagents.org` is an intended domain configured in the source, **not a verified live website**. If you see "Site can't be reached", use the [deployment & DNS repair instructions](apps/website/DEPLOYMENT.md). A public hosting deployment and domain connection are required before this button can work.

Local-first, privacy-preserving multi-agent automation platform for creators, social growth, and personal workflows.

## Architecture

- **Local Runtime (`services/local-runtime/`)**: Python FastAPI backend with SQLite async persistence, APScheduler job recovery, Privacy Firewall, multi-provider AI Router (Ollama / Gemini / OpenAI-compatible), and 29 specialized agents coordinated by `MasterAgent`.
- **Dashboard (`apps/dashboard/`)**: React + TypeScript + Tailwind CSS desktop dashboard with visual node-based workflow editor.
- **Desktop Shell (`apps/windows/`)**: Electron wrapper for Windows with system tray controls and emergency stop.
- **Mobile Companion (`apps/android/`)**: Android companion app with secure device pairing.

## Quick Start (Backend — Safe Loopback Default)

```bash
cd services/local-runtime
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

> **Security Default:** Local installations bind exclusively to `127.0.0.1` (loopback). For explicit LAN pairing with the Android companion, pass `--host <your-lan-ip>` and confirm pairing via a time-limited code in `/devices/pair`.

Once running, open the interactive API docs at `http://127.0.0.1:8000/docs`.

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
