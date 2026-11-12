# Release and Signing Guide (Windows & Google Play)

## 1. Windows Desktop Installer (`apps/windows/`)

### Build & Package Steps
```powershell
# 1. Generate .ico and .png assets (requires Pillow)
python packages/brand-assets/icons/generate_icons.py

# 2. Build packages, dashboard, and Electron app + NSIS/Portable EXEs
.\scripts\package-release.ps1
```
Output artifacts appear in `apps/windows/release/`:
- `JavoAgents-0.1.0-x64.exe` (NSIS Installer)
- `JavoAgents-Portable-0.1.0-x64.exe` (Portable Executable)

### Windows Code Signing (Recommended Before Public Distribution)
Without an Authenticode certificate, Windows SmartScreen shows an "Unknown Publisher" prompt.
To sign in CI or locally:
1. Obtain an OV or EV Code Signing Certificate (e.g., DigiCert, Sectigo, or Azure Trusted Signing).
2. Set environment variables before running `electron-builder`:
   - `CSC_LINK`: Path or base64 of `.pfx` certificate (or Azure Trusted Signing profile)
   - `CSC_KEY_PASSWORD`: Certificate password
3. Verify signature with `signtool verify /pa /v apps/windows/release/JavoAgents-0.1.0-x64.exe`.

---

## 2. Google Play Readiness (`apps/android/`)

### Pre-Submission Checklist
1. **Signing Keystore**: Generate a release upload keystore (`keytool -genkey -v -keystore javo-upload.jks ...`) and opt into **Play App Signing**. Never commit `.jks` or `keystore.properties` to Git.
2. **Build AAB**:
   ```bash
   cd apps/android
   ./gradlew bundleRelease
   ```
3. **Permissions Justification** (see `apps/android/play-store/permissions-justification.md`):
   - `RECORD_AUDIO` + `FOREGROUND_SERVICE_MICROPHONE`: Used strictly when user taps Push-to-Talk in Voice Mode.
   - `CAMERA`: Used strictly for scanning Windows pairing QR code.
   - `POST_NOTIFICATIONS`: Approval alerts and task completion notices.
4. **Data Safety & Policy Compliance**:
   - No dynamic executable code downloading (`DexClassLoader` / remote scripts).
   - No background audio recording without visible notification.
   - Accurate Data Safety disclosure (`apps/android/play-store/data-safety.md`).
5. **Internal Testing Track**: Upload `.aab` to Google Play Console Internal Testing first, verify on physical Android 12–15 devices, then promote to Closed/Production.
