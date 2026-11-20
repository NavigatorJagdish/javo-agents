# Saved accounts and protected legacy credentials

This build saves actual local account records and separate brand profiles.
Official OAuth, capability discovery, token refresh/revocation and live
publishing remain unavailable. Creating a record, storing a token or importing
an old `connected` flag never verifies a platform connection. The API reports
`status: disconnected` and `connection_verified: false`; `reported_status`
retains the historic database flag for diagnosis only.

The owner token can access `local-owner` and the old synthetic `default-user`
alias. Arbitrary other owners cannot be selected. New content/accounts share
the canonical owner; old default-user content can still be scheduled to the
same owner's new records. This is single-owner authorization, not completed
multi-user authentication or secure device pairing.

## Credential protection

At startup, a bounded pass examines up to 100 candidate owned accounts,
prioritizing nonempty legacy token columns. It stops accepting further accounts
after five seconds; an individual atomic storage operation can take longer.
The Accounts screen also offers a per-account retry for legacy credentials.
Recognized credential keys nested in old account metadata are archived inside
the encrypted record with their JSON-pointer location. Unrelated metadata
stays in the source. Free-form text is not comprehensively classified.

Nonempty legacy values are saved atomically to an account-specific authenticated
Fernet document and reopened/verified **before** clearing SQL token columns or
recognized credential metadata. A crash before SQL commit leaves the source
available and the next matching migration can retry. Conflicting copies,
unreadable ciphertext, missing keys, oversized/invalid values or failed writes
keep the original SQL values for recovery. Existing protected values cannot
be silently replaced by differing legacy values. Failed protection does not
fall back to plaintext storage or mark the account connected.

`JAVO_ACCOUNT_CREDENTIALS_DIR` can select a private directory; the default is
`account-credentials` beside `JAVO_PROVIDER_CONFIG_PATH`. Account filenames
are hashes; configured keys use separate per-account/social/provider domains.
Without a configured secret, Windows protects a random per-document key using
current-user DPAPI. Both ciphertext and wrapped key must stay with the original
Windows user/profile. Even moving both files to another account's storage path
fails the account binding. Other platforms require a retained high-entropy
`JAVO_ENCRYPTION_KEY` of at least 32 characters; there is no plaintext fallback.

Owner APIs return availability/protection/expiry flags, never raw credentials.
They accept no manual access/refresh token fields. Arbitrary old metadata is
retained privately but only reviewed public account identifiers are returned.
SQLite `secure_delete` is enabled for runtime connections; tests check that
known migrated values disappear from the current database file. This does not
claim forensic erasure from old backups, journal copies, disk snapshots or SSDs.

Removing credentials writes a protected tombstone and clears known legacy
fields. It does not contact a platform, revoke a grant or delete older backups.
Locked storage must be recovered before removal; it is never reset silently.
Unused account removal also removes its brand profile. Accounts with linked
tasks or schedules return 409 so execution history survives; credentials can
be removed separately. Account name/brand data remain normal SQLite data;
this increment is not whole-profile/database encryption.

## Saved forms and API

Accounts provides paginated real records, add/edit, per-account brand name,
voice, audience and pillars, credential protection state and explicit removal
confirmations. Errors stay visible rather than becoming simulated success.
No followers, platform analytics, rate-limit caps or OAuth results are invented.
The related setup steps point to these saved forms; finishing the guide does
not certify models or other unfinished capabilities.

- GET/POST `/api/accounts/`; GET/PUT/DELETE `/api/accounts/{id}`.
- GET/PUT `/api/accounts/{id}/brand-profile`.
- POST `/api/accounts/{id}/credentials/migrate`.
- DELETE `/api/accounts/{id}/credentials`.
- POST `/api/accounts/{id}/oauth/initiate` returns 501 until official setup,
  persisted state, PKCE/callback validation and permission checks are completed.

Database-only snapshots exclude the separate credential documents and keys,
AI-provider vault, usage ledger and media. Full encrypted profile recovery,
backup-key portability and platform grant revocation still need implementation.

## Evidence boundaries

The account tests exercise actual HTTP/SQLite restart, synthetic legacy-token
migration, nested metadata, conflict/failure preservation, owner isolation,
history retention and account-bound encrypted file reads. Windows-only tests
use real current-user DPAPI. `scripts/verify-dashboard.py --scenario accounts`
seeds explicitly synthetic old records before starting the real source/frozen
runtime, then checks encrypted migration, API redaction, unavailable OAuth,
credential removal and record/brand create/edit/reload/removal in Chrome.
This is local storage/UI evidence, not live social authentication or posting.
