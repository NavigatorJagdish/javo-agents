# Changelog

All notable changes to Javo Agents are documented in this file.

## [0.1.0] - 2026-11-12

### Added
- **Brand Assets (`packages/brand-assets/`)**: Hexagonal shield logo suite (Primary, Light, Mark, Monochrome), Favicon, Windows App Icon + Pillow `.ico`/`.png` generator script, Dark & Light Splash screens, and Brand Guidelines.
- **Shared Packages (`packages/`)**:
  - `@javo/shared-types` aligned with Python FastAPI SQLAlchemy/Pydantic models.
  - `@javo/api-client` typed REST + WebSocket client with reconnect backoff.
  - `@javo/workflow-schema` 16-node workflow registry and DAG/Autopilot graph validator.
  - `@javo/policy-engine` deterministic Supervised Autopilot, permission scope, privacy firewall, and zero-cost guardrails.
- **Windows Desktop Shell (`apps/windows/` & `scripts/`)**: Electron shell with single-instance lock, system tray Pause/Resume/Emergency Stop menu, FastAPI auto-launcher, hardware detector, NSIS/Portable builder config, and PowerShell setup/start/build/package scripts.
- **Skills & Model Profiles (`skills/`, `models/`)**: Skill manifest JSON schema, `social-caption-optimizer`, `hindi-hinglish-hook-writer`, AST + isolated subprocess sandbox runner with env credential scrubbing and trust scoring, plus `ollama-8gb-profiles.json`.
- **Documentation & CI/CD (`docs/`, `.github/`)**: Architecture + ADRs, 20-threat Threat Model, Key Recovery guide, 7 setup guides, Security/Privacy/API/Release docs, 4 GitHub Actions workflows, and Issue/PR templates.
