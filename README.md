# Javo Agents

[![Open Javo Website](https://img.shields.io/badge/OPEN_JAVO_WEBSITE-00C8FF?style=for-the-badge&logo=googlechrome&logoColor=white)](https://navigatorjagdish.github.io/javo-agents/)

**[🌐 Open Javo Website](https://navigatorjagdish.github.io/javo-agents/)** · [🚀 GitHub Pages Setup](apps/website/GITHUB_PAGES.md) · [View Website Source](https://github.com/NavigatorJagdish/javo-agents/tree/main/apps/website) · [Website Documentation](https://github.com/NavigatorJagdish/javo-agents/tree/main/docs)

> **GitHub Pages deployment succeeded:** [Open Javo Website](https://navigatorjagdish.github.io/javo-agents/) · [Successful GitHub Actions run](https://github.com/NavigatorJagdish/javo-agents/actions/runs/43461141799). GitHub reports that the site was published; if the link temporarily does not load, retry after GitHub Pages propagation.

Local-first, privacy-preserving multi-agent automation platform for creators, social growth, and personal workflows.

## Architecture

- **Local Runtime (`services/local-runtime/`)**: Python FastAPI backend with SQLite async persistence, APScheduler job recovery, Privacy Firewall, multi-provider AI Router (Ollama / Gemini / OpenAI-compatible), and 29 specialized agents coordinated by `MasterAgent`.
- **Dashboard (`apps/dashboard/`)**: React + TypeScript + Tailwind CSS desktop dashboard with visual node-based workflow editor.
- **Desktop Shell (`apps/windows/`)**: Electron wrapper for Windows with system tray controls and emergency stop.
- **Mobile Companion (`apps/android/`)**: Android companion app with secure device pairing.

## Quick Start (Backend)

Set a private, random `JAVO_OWNER_ACCESS_TOKEN` (at least 32 characters) before starting. API requests require `Authorization: Bearer <token>`. The desktop shell generates a per-launch token automatically. Never commit a real token. See `docs/REBUILD_STATUS.md` for current limitations; historic verification below is not a release certification.

```bash
cd services/local-runtime
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
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

Runtime control is persisted in JAVO_CONTROL_STATE_PATH (default ./runtime-control.json). First startup or unreadable state starts paused; explicitly resume through the owner-authorized control endpoint or dashboard. Pause/emergency state is restored on restart. A failed state write returns an error: current-process stopping still takes effect, but restart durability cannot be guaranteed after a storage failure. Keep the state path on durable writable storage.
