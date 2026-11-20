# Persisted provider configuration

Owner-authenticated Settings can save a provider model/endpoint, enabled state,
replacement key, default provider and maximum requested output tokens. A save
does not contact a model or test the provider. Blank replacement-key input
preserves the saved key; the separate removal action deletes the saved value
and disables the provider. Removal also overrides an environment key rather
than silently falling back to it.

The owner API and AI router read the same configuration. Metadata responses
report only whether a key exists. Validation responses omit raw input/context,
and Gemini authentication is sent in its header rather than a logged URL.
Remote custom endpoints require HTTPS and cannot contain URL credentials,
queries or fragments. Local Ollama is restricted to loopback addresses.

The default `provider-config.enc` is an authenticated Fernet document. Atomic
replacement and cross-process locking prevent partial saves/lost updates.
On Windows, absent a configured encryption secret, a generated encryption key
is protected using current-user DPAPI and kept in a sibling `.key.dpapi` file.
It is not machine-wide protection. Moving these files to another user or
machine is not a recovery method; retain the original profile or re-enter
credentials. An existing vault with a missing/broken key is never reset
automatically.

For other platforms, configure a high-entropy persistent `JAVO_ENCRYPTION_KEY`
of at least 32 characters; no unprotected key-file fallback is used. That
configured key can also be chosen on Windows. The provider encryption key is
derived in a separate domain from database backup encryption. Retain recovery
secrets outside the source tree; do not use an ordinary human password.

`JAVO_PROVIDER_CONFIG_PATH` selects the encrypted file. Desktop defaults live
under writable per-user runtime data; a portable QA profile is explicit.
Keep custom locations outside source repositories. Source checkpoints exclude
encrypted runtime documents and wrapped keys. Database snapshots currently do
not include the provider vault or its OS-protected key.

Cloud budgets remain zero by default. Positive budget changes through this
API remain blocked until a durable spending ledger and pricing controls are
implemented. Provider configuration is not a guarantee of model availability,
free quota, spending bounds or successful generation. No live cloud request is
made by save/remove operations or by the automated key tests.

API:

- GET `/api/settings/provider-storage` reports storage availability/protection.
- GET `/api/settings/ai-providers` returns safe metadata.
- PUT `/api/settings/ai-providers/{name}` saves supported fields.
- DELETE `/api/settings/ai-providers/{name}/credentials` removes/disables keys.
- PUT `/api/settings/` supports AI defaults and zero budgets. Resource-control
  and logging changes are not hot-applied through this API.

Platform-neutral tests cover restart reads, tampering, wrong keys, failed
writes, concurrent saves, metadata redaction, removal tombstones, routing and
HTTP validation. Windows CI additionally exercises real current-user DPAPI.
The browser smoke exercises encrypted save/reload/remove without cloud calls.
