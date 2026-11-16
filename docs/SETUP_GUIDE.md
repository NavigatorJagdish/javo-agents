# Measured setup guide and local model check

The development guide no longer invents CPU/GPU/RAM/disk specifications,
marks unperformed diagnostics passed, accepts unsaved bot tokens or pretends
that a waveform tests a microphone. Its progress bar shows guide position,
not feature completion. Finishing the guide opens the dashboard; it does not
certify the product, start autopilot or install a model.

Hardware reads `/api/health/system`. It reports actual runtime-host CPU,
memory, system-drive usage and selected resource profile. GPU/VRAM,
instruction-set support and 8GB/larger-system workload benchmarks are unknown.
Runtime service diagnostics run their real database/scheduler/module checks;
an imported AI router is explicitly not proof of model availability/generation.
Database errors use fixed messages rather than raw paths or exceptions.

AI Setup shares the real encrypted provider editor with Settings. Only an
explicit Save writes configuration. Its local model check also appears in
Settings and reads the saved configuration. Content/account/brand steps point
to actual saved forms. Runtime control is read from the real API; permission
changes and resuming remain separate actions. Telegram, audio and full profile
recovery are labelled unfinished. No bot token or microphone access is collected
by these guide steps. Privacy text distinguishes encrypted credentials from
ordinary SQLite account/brand/content data.

## Explicit local inventory check

POST `/api/settings/ai-providers/ollama/check` requires the owner token and
performs a GET to the saved, validated loopback endpoint's `/api/tags`.
It never calls a cloud API, generates text, pulls a model or changes settings.
It ignores environment proxies, refuses redirects/compressed responses,
bounds total time to three seconds, caps response bytes at1MiB and inventory
at1000 models, and displays at most100 validated names. It sends no API key.
Disabled/invalid configuration makes no connection. Fixed result messages
exclude raw errors, endpoint URLs and server response bodies.

`available` means the configured model name is present in the loopback
service's reported list; untagged names match `:latest`. It is not proof of
local execution, model licensing/quality, successful generation, offline
availability or sufficient resources. Other results are `model_missing`,
`disabled`, `invalid_configuration` and `unavailable`. `generation_verified`
is always false. Results show a check timestamp and reset when saved local
configuration changes.

The protocol follows the official [Ollama model-list API](https://docs.ollama.com/api/tags).
No current default model is automatically downloaded or recommended from a
fabricated hardware report.

`scripts/verify-dashboard.py --scenario setup` exercises every guide page
with a real temporary runtime/database and clearly synthetic loopback model
inventory. It verifies actual measurements, encrypted save/authenticated reload,
model-present/model-missing results, visible capability limits and a390px
layout. Model-inventory unit tests cover invalid endpoints, redirect refusal,
bad/oversized payloads, disabled/locked configuration, timeout, cancellation,
redacted failures and owner authorization. These are acceptance checks for
the guide/inventory feature, not real-model performance certification.
