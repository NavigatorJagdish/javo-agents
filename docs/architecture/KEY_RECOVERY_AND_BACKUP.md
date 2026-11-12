# Key Recovery and Backup Guide

## 1. What Needs to Be Backed Up

Javo Agents stores all user state locally inside `services/local-runtime/` (or `%APPDATA%\JavoAgents\` when packaged):

1. **Primary Database**: `javo_agents.db` (tasks, goals, workflows, agent configs, brand profiles, audit logs)
2. **Scheduler Store**: `scheduler_jobs.db` (APScheduler persistent triggers)
3. **Configuration & Keys**: `.env` (contains `JAVO_SECRET_KEY`, `JAVO_ENCRYPTION_KEY`, optional Gemini/Telegram tokens)
4. **Custom Skills**: `skills/community/` and any user-modified manifests
5. **Content Assets**: User-selected `content_root` directory

> [!CAUTION]
> **Never lose `JAVO_ENCRYPTION_KEY`!** Encrypted OAuth tokens in `javo_agents.db` cannot be decrypted without the matching encryption key.

---

## 2. Creating an Encrypted Backup

### Option A: Dashboard Settings UI
1. Open **Settings → Backup & Restore**.
2. Click **Create Backup Archive**.
3. Choose a strong backup passphrase (stored in your password manager, **not** on the same drive).
4. Save the generated `.javobak` file to an external USB drive or private cloud folder.

### Option B: Manual Backup (PowerShell)
```powershell
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Dest = "$env:USERPROFILE\Documents\JavoBackups\backup-$Stamp"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

Copy-Item "d:\antigravityproject\javo-agents\services\local-runtime\javo_agents.db" $Dest
Copy-Item "d:\antigravityproject\javo-agents\services\local-runtime\scheduler_jobs.db" $Dest -ErrorAction SilentlyContinue
Copy-Item "d:\antigravityproject\javo-agents\services\local-runtime\.env" $Dest -ErrorAction SilentlyContinue
```

---

## 3. Key Rotation Procedure

1. Pause Autopilot from the Windows System Tray or Dashboard.
2. Back up the current database and `.env` file.
3. Generate a new 32-byte URL-safe Fernet key:
   ```powershell
   python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
   ```
4. Use the Settings → Security → **Rotate Encryption Key** tool (re-encrypts stored social tokens atomically).
5. Re-pair Android devices if `JAVO_SECRET_KEY` was rotated.

---

## 4. Disaster Recovery (If Key Is Lost)

If `JAVO_ENCRYPTION_KEY` is permanently lost:
1. Stop Javo Agents (`Quit` from Tray).
2. Restore `javo_agents.db` (workflows, goals, content metadata, and memory remain readable).
3. Generate a fresh `.env` with a new `JAVO_ENCRYPTION_KEY`.
4. Re-connect Social Accounts (YouTube, Instagram, Facebook) via OAuth and re-pair your Android phone via QR code.
