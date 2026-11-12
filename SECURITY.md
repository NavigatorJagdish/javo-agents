# Security Policy

## Local-First Privacy Guarantees

Javo Agents is designed so sensitive credentials, private keys, and raw tokens never leave the local runtime:

1. **Credential Vault**: Social OAuth tokens and API keys are encrypted at rest using Fernet symmetric encryption (`app/core/security.py`).
2. **Privacy Firewall**: Outbound prompts are inspected for secrets and PII (`app/core/privacy_firewall.py`). Restricted payloads are blocked from cloud egress and routed locally via Ollama.
3. **Device Pairing**: Companion devices authenticate through short-lived 6-character pairing codes, challenge nonces, and revocable HMAC-signed tokens.
4. **Emergency Stop**: `POST /security/emergency-stop` halts task queuing, drains pending jobs, and logs an audit entry.

## Reporting a Vulnerability

Please do not open public GitHub issues for security vulnerabilities.
Instead, send a detailed report to the maintainers via the security contact listed in the repository or use GitHub's private Security Advisory feature.

Include:
- Affected component and version
- Reproduction steps or proof of concept
- Potential impact and suggested mitigation
