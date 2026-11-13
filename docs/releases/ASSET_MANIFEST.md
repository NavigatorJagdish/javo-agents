# Javo Agents v0.1.0-alpha — Tested Asset Manifest & Provenance

**Build Date:** 2026-11-13  
**Repository:** `NavigatorJagdish/javo-agents` (Private)  
**Version:** `0.1.0-alpha`  
**Working PR:** `#1` (`fix/android-ci-and-production-hardening`)  
**Draft Release ID:** `443379038` (`v0.1.0-alpha`)

---

## 1. Verified Release Package Artifacts & Checksums

The following artifacts have been built, verified, and attached directly to GitHub Draft Release `443379038` on the private repository `NavigatorJagdish/javo-agents`:

| Asset File | Target Architecture | Package Type | File Size | Verified SHA-256 Checksum | Release Asset ID / Status |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `JavoAgents-0.1.0-x64.exe` | Windows 10/11 x64 | NSIS Setup Installer | 81,863,491 bytes (~78 MB) | `f0cd79c0144701bb7a9f2fa8852f54f51ad0b5f606e4aa5b6b26cb388ddba1ff` | Asset ID: `742215572` (Verified in Storage) |
| `JavoAgents-Portable-0.1.0-x64.exe` | Windows 10/11 x64 | Standalone Portable PE | 81,635,860 bytes (~77.8 MB) | `9aecb106a57d27567fd08980663431271440c1516076663ab8999b93fd927127` | Asset ID: `742215570` (Verified in Storage) |
| `SHA256SUMS.txt` | ASCII Text | Checksum Ledger | 193 bytes | Verified from build output | Asset ID: `742215571` (Verified in Storage) |
| `javo-agents-android-v0.1.0-alpha-debug.apk` | Android 10+ (API 29+) | Debug Test APK | 19,127,677 bytes (~18.2 MB) | `5ab88a647f3ec223a70aa6f5d7fbf67a4dab4f2481ac1ff30f667114c3f1bbb8` | Asset ID: `742231566` (Verified in Storage) |
| `javo-agents-android-v0.1.0-alpha-release-unsigned.apk` | Android 10+ (API 29+) | Release APK (Unsigned) | 1,741,367 bytes (~1.66 MB) | CI Verification Package | Asset ID: `742231738` (Verified in Storage) |

---

## 2. Release Provenance & Checksum Reconciliation

### Why CI Run Hashes Differ from Packaged Release Binaries
1. **Packaging Non-Determinism in Electron Builder:** Electron-builder embeds build timestamps, temporary UUIDs, and host environment paths into the NSIS 7z archive container on each invocation. As a consequence, running `electron-builder` on an ephemeral GitHub Actions `windows-latest` runner generates a fresh binary hash (e.g. `954ee4...` in run `43285582744` or `2005c7...` in run `43284085211`) that differs from the local release build (`5d6f13...`).
2. **Delivery Decoupling:** In previous CI runs, the step `actions/upload-artifact@v4` was rejected due to the GitHub account's 500 MB Actions storage quota, while `continue-on-error: true` concealed the upload failure. The only binaries actually delivered to GitHub storage are the verified packages attached to Draft Release `443379038`.
3. **Cryptographic Ledger Integrity:** `apps/windows/release/SHA256SUMS.txt`, `apps/website/src/data/site.ts`, and this manifest are strictly bound to the exact binaries hosted on Draft Release `443379038`.

---

## 3. Desktop Authenticated Control Remediation

### The Vulnerability Identified
In `apps/windows/src/backendManager.ts`, `callControlEndpoint(endpoint, body)` previously issued plain HTTP POST requests without an `Authorization: Bearer <owner_token>` header. Because FastAPI enforces `Depends(require_owner)` on `/security/pause`, `/security/resume`, and `/security/emergency-stop`, all requests were rejected with `HTTP 401 Unauthorized`. The desktop shell ignored the failure and falsely reported UI actions as successful.

### The Remediation Implemented
1. **Secure In-Memory Token Management:** `LocalRuntimeManager` generates or loads the durable owner token (`crypto.randomBytes(32).toString('base64url')` or `JAVO_OWNER_TOKEN`) and injects `JAVO_OWNER_TOKEN` into the Python backend process `env`.
2. **Authenticated Control Requests:** `callControlEndpoint` includes `Authorization: Bearer <token>` on all requests.
3. **Honest Status & Error Reporting:** `callControlEndpoint` checks `res.ok`, records server error details on failure, and returns `false` on non-2xx status. The UI only records state transitions and notifications when `ok === true`.
4. **Zero Query String / Storage Leakage:** Auth credentials are exchanged between Electron main and the React dashboard via Electron IPC (`javo:get-api-config`) in-memory, without exposing tokens in browser URLs (`?token=...`) or browser localStorage.
5. **Verified by Regression Test:** Tested and confirmed passing in `test_desktop_control_endpoints_require_owner_token` in `tests/security/test_security_remediation.py`.

---

## 4. Windows Standalone Execution & Python Runtime Handling

### Problem
Clean Windows installations lacking Python on PATH would fail on `spawn("python")` with `ENOENT`, which was previously unhandled and left the shell hanging on healthcheck timeout.

### Solution
1. **Multi-Path Python Search:** `resolvePythonExecutable()` in `backendManager.ts` inspects:
   - `process.env.JAVO_PYTHON_PATH`
   - Bundled Python paths in `resources/python` and `local-runtime/.venv`
   - Windows user Python installations (`%LOCALAPPDATA%\Programs\Python\Python311`, `Python312`, `Python310`)
   - System installations (`C:\Program Files\Python31*`, `C:\Python31*`)
   - PATH fallback (`python`)
2. **Graceful ENOENT Trap:** Spawning errors are caught and logged as: `"Python runtime not found. Please install Python 3.10+ from https://www.python.org or set JAVO_PYTHON_PATH."`
3. **Actionable UI Disclosure:** `apps/windows/public/fallback.html` displays the runtime diagnostic alert with actionable resolution steps when offline.

---

## 5. How to Download Private Alpha Packages

Because `NavigatorJagdish/javo-agents` is a **Private Repository**, unauthorized or unauthenticated requests to GitHub release URLs will receive an HTTP 404 response.

To download:
1. Ensure you are signed into GitHub with an account that has **collaborator access** to `NavigatorJagdish/javo-agents`.
2. Access the **Private Release Hub**:
   `https://github.com/NavigatorJagdish/javo-agents/releases`
3. Under **Javo Agents v0.1.0-alpha (Private Alpha Test)**, click the desired asset:
   - `JavoAgents-0.1.0-x64.exe` (NSIS Installer)
   - `JavoAgents-Portable-0.1.0-x64.exe` (Portable Executable)
   - `javo-agents-android-v0.1.0-alpha-debug.apk` (Android Test APK)
   - `SHA256SUMS.txt` (Cryptographic verification checksums)
4. Verify checksums locally:
   ```powershell
   Get-FileHash .\JavoAgents-0.1.0-x64.exe -Algorithm SHA256
   ```
