# Javo Agents

[![Open Javo Website](https://img.shields.io/badge/OPEN_JAVO_WEBSITE-00C8FF?style=for-the-badge&logo=googlechrome&logoColor=white)](https://navigatorjagdish.github.io/javo-agents/)

**[🌐 Open Javo Website](https://navigatorjagdish.github.io/javo-agents/)** · [🚀 GitHub Pages Setup](apps/website/GITHUB_PAGES.md) · [View Website Source](https://github.com/NavigatorJagdish/javo-agents/tree/main/apps/website) · [Website Documentation](https://github.com/NavigatorJagdish/javo-agents/tree/main/docs)

> **GitHub Pages deployment succeeded:** [Open Javo Website](https://navigatorjagdish.github.io/javo-agents/) · [Successful GitHub Actions run](https://github.com/NavigatorJagdish/javo-agents/actions/runs/43461141799). GitHub reports that the site was published; if the link temporarily does not load, retry after GitHub Pages propagation.

Local-first, privacy-preserving multi-agent automation platform for creators, social growth, and personal workflows.

## Rebuild status

This is an unfinished development build. [Draft PR #5](https://github.com/NavigatorJagdish/javo-agents/pull/5)
contains authenticated controls, durable pause/stop, reviewed content approval,
timed simulation receipts and encrypted snapshots. Live social posting remains
disabled. Windows CI has verified the standalone runtime, packaged app and
NSIS install/uninstall/reinstall using an isolated QA profile at earlier checkpoints.
A fresh-install crash was corrected by updating the builder to 26.9.0; later
Windows checks passed the full install/uninstall/reinstall cycle. This is not a
signed release or certification of every machine and feature.

Provider models, enabled state, defaults and credentials now share encrypted
persistence between Settings and the AI router. Windows uses current-user
key protection; other platforms require a retained encryption secret. See
[provider configuration and recovery boundaries](docs/PROVIDER_CONFIGURATION.md).
Positive budget increases remain blocked pending verified pricing and explicit
paid activation; saved usage accounting alone does not authorize spending.
The [text companion](docs/COMPANION.md) now uses real runtime controls and configured AI
with bounded context and cancellation. The [voice and creation studio](docs/CREATOR_AND_INTEGRATIONS.md)
adds local Kokoro/Whisper speech, original effects and reviewed optional media-service integration.
The [Goals screen](docs/GOALS.md) uses saved measurements and milestones;
[AI usage accounting](docs/AI_USAGE.md) survives restart. The
[AI Team execution queue](docs/AGENT_EXECUTION.md) supports real saved-goal and
budget summaries with cancellation and receipts. Remaining specialists are
explicitly unavailable for execution until their paths are completed.
See the [current delivery review, remaining work and improvements](docs/CURRENT_DELIVERY_REVIEW.md)
for the complete acceptance boundaries and prioritized next work.
The [Accounts screen](docs/SOCIAL_ACCOUNTS.md) saves real account/brand records
and protects legacy credentials using account-bound encrypted storage. Stored
credentials remain unverified; official platform sign-in is unavailable.
The [setup guide](docs/SETUP_GUIDE.md) uses measured hardware/service status,
saved provider forms and an explicit loopback model-list check. It no longer
certifies unavailable audio, Telegram or platform connections.
The [workflow editor](docs/WORKFLOWS.md) saves graphs with revision history,
conflict recovery and reviewed manual local-text runs. Supported paths use
Trigger, local AI Prompt, Delay and End; other catalog nodes remain save-only.
See [best use and reproduced bug fixes](docs/BEST_USE_AND_BUG_REVIEW.md).
External tools use [scoped reviewed integrations](docs/CREATOR_AND_INTEGRATIONS.md)
and original [n8n workflow templates](docs/N8N_WORKFLOWS.md). Catalog entries are
not activated runtimes. See the [license boundary](docs/THIRD_PARTY_BOUNDARY.md)
and [current defensive review](docs/security/SECURITY_REVIEW_20261120.md).
Android, full workflows/analytics, official live connectors and complete
specialist functionality remain under development. See [evidence](docs/REBUILD_STATUS.md).

## Architecture

- **Local Runtime (`services/local-runtime/`)**: Python FastAPI backend with SQLite async persistence, APScheduler job recovery, Privacy Firewall, multi-provider AI Router (Ollama / Gemini / OpenAI-compatible), and 29 specialized agents coordinated by `MasterAgent`.
- **Dashboard (`apps/dashboard/`)**: React + TypeScript + Tailwind CSS desktop dashboard with visual node-based workflow editor.
- **Desktop Shell (`apps/windows/`)**: Electron wrapper for Windows with system tray controls and emergency stop.
- **Mobile Companion (`apps/android/`)**: Companion source under development; complete device pairing and end-user functionality remain unverified.

## Quick Start (Backend)

Set a private, random `JAVO_OWNER_ACCESS_TOKEN` (at least 32 characters) before starting. API requests require `Authorization: Bearer <token>`. The desktop shell generates a per-launch token automatically. Never commit a real token. See `docs/REBUILD_STATUS.md` for current limitations; historic verification below is not a release certification.

```bash
cd services/local-runtime
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Once running, open the interactive API docs at `http://localhost:8000/docs`.

## Key Features

- **29 Specialist Definitions + Master Orchestrator**: Registered modules; their production functionality is still being completed and verified.
- **Privacy Firewall**: Automatic PII/secret classification and egress blocking before any request reaches cloud AI providers.
- **Local AI First**: Ollama adapter with zero default cloud budgets. Actual model availability and durable cost controls still require verification/work.
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
