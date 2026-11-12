# Google Play Data Safety Declaration — Javo Agents

## Overview
Javo Agents is a **local-first, user-controlled** application. There are **no developer-operated cloud tracking servers**, **no third-party advertising SDKs**, and **no analytics brokers**.

## Data Collection & Handling Matrix

| Data Type | Collected by Developer? | Purpose | Storage & Encryption | Shared with Third Parties? |
| --- | --- | --- | --- | --- |
| **Audio / Voice Input** (`RECORD_AUDIO`) | No (processed on-device or sent directly to user's paired Windows PC) | Push-to-talk voice commands in Voice Mode | Ephemeral; never persisted to developer servers | No (unless user explicitly configures their own Gemini API key) |
| **User Drafts, Goals & Approvals** | No | Offline content drafting & approval queue | Local SQLite via Room (`javo_agents.db`), excluded from cloud backup | Synced only to the user's explicitly paired Windows Local Runtime |
| **Pairing Tokens & API Keys** | No | Mutual auth with Windows PC & optional user-supplied Gemini API | Encrypted with AES-256-GCM via Android Keystore + `EncryptedSharedPreferences` | Sent only to user's paired Windows host or Google Gemini API if enabled |
| **Device Identifier** | No | Distinguish paired Android devices in Windows Security Center | Random UUID stored in `EncryptedSharedPreferences` | Sent only to user's paired Windows host |
| **Crash / Diagnostics Reports** | No | Local troubleshooting & user-initiated export | Stored locally on-device unless user manually shares | No |

## Security Practices
- **Encryption in transit**: HTTPS enforced globally (`network_security_config.xml` sets `cleartextTrafficPermitted="false"` on `<base-config>`, permitting cleartext only on local loopback `localhost`/`127.0.0.1`/`10.0.2.2` for local development).
- **Encryption at rest**: `KeystoreManager` wraps secrets using `AndroidKeyStore` AES-256-GCM and `EncryptedSharedPreferences`.
- **Cloud Backup Exclusion**: `data_extraction_rules.xml` and `backup_rules.xml` explicitly exclude `javo_secure_prefs.xml` and `javo_agents.db` from automatic cloud backups.
- **Data Deletion**: Users can wipe all local Room tables and Keystore secrets in one tap via **Privacy & Data -> Delete All Local Data & Secrets**.

## Google Play Policy Compliance
- **No Unrestricted Executable Code Downloading**: All 29 agents are declarative configurations/routes; Android never downloads or executes dynamic DEX/native code.
- **No Fake Engagement or Misleading Claims**: Analytics screen explicitly separates local/runtime metrics from unavailable external metrics (`Sample / Unavailable`).
