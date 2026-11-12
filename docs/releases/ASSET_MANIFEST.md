# Javo Agents v0.1.0-alpha — Tested Asset Manifest

**Build Date:** 2026-11-13  
**Repository:** `NavigatorJagdish/javo-agents` (Private)  
**Version:** `0.1.0-alpha`  
**Commit SHA:** Verified on working branch `fix/android-ci-and-production-hardening`  

---

## 1. Windows Desktop Package Artifacts

| Asset File | Target Architecture | Package Type | File Size | Verified SHA-256 Checksum | Provenance / CI Workflow |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `JavoAgents-0.1.0-x64.exe` | Windows 10/11 x64 | NSIS Installer | 82,823,342 bytes (~79 MB) | `5d6f13f07a3b84957814f5a079c8de78ee14bbfbae91eda5764d03df1e8e8fd0` | Built via `pnpm run dist:win` & `.github/workflows/ci-windows.yml` |
| `JavoAgents-Portable-0.1.0-x64.exe` | Windows 10/11 x64 | Portable Executable | 82,570,280 bytes (~78.7 MB) | `c8e092aa339137d615e474ca0b7ed598f0cc74bd76cca10d82c601620f51b7e7` | Built via `pnpm run dist:win` & `.github/workflows/ci-windows.yml` |
| `win-unpacked/Javo Agents.exe` | Windows 10/11 x64 | Unpacked PE Binary | 188,784,128 bytes | `4f839a05005fec5a91bcba39dffb52cb8b5840bf247343e74c84eb63e00787fa` | Unpacked Electron shell container |
| `SHA256SUMS.txt` | Text / ASCII | Checksum Ledger | 388 bytes | N/A | Included in release package |

### Windows Packaging Verification
- **PE Executable Signature:** Verified (`MZ` header and `PE\0\0` signature at offset 0x3c).
- **Bundled Resource Containment:** Verified `resources/dashboard/` (React SPA), `resources/local-runtime/` (FastAPI backend + 29 specialist agents), `resources/icons/` (app icons), and `app.asar`.
- **Runtime Lifecycle:** Verified background startup on dynamic port `51740`, clean healthcheck HTTP 200 at `/health/`, and clean SIGTERM shutdown.

---

## 2. Android Companion Package Artifacts

| Asset File | Target OS / API | Package Type | Provenance / CI Workflow | Verification Notes |
| :--- | :---: | :---: | :--- | :--- |
| `javo-agents-android-v0.1.0-alpha-debug.apk` | Android 10+ (API 29+) | Debug Test APK | `.github/workflows/ci-android.yml` (`gradle assembleDebug`) | Test APK for internal testing and sideloading |
| `javo-agents-android-v0.1.0-alpha-release-unsigned.apk` | Android 10+ (API 29+) | Unsigned Release APK | `.github/workflows/ci-android.yml` (`gradle assembleRelease`) | Built with ProGuard/R8 release rules |
| `javo-agents-android-v0.1.0-alpha-release-unsigned.aab` | Android 10+ (API 29+) | App Bundle (AAB) | `.github/workflows/ci-android.yml` (`gradle bundleRelease`) | Store-ready architecture (signing withheld) |
| `build-metadata.json` | JSON | CI Build Metadata | `.github/workflows/ci-android.yml` | Git commit, branch, and timestamp stamp |

### Android Packaging Verification
- **Automated Unit Tests:** `OfflineDraftRepositoryTest.kt`, `KeystoreManagerTest.kt`, `PairingTokenValidatorTest.kt` passing.
- **Android Lint:** `gradle lintDebug` passed with 0 errors.
- **R8 ProGuard Rules:** Verified `-dontwarn` rules for `com.google.errorprone.annotations.*` in `apps/android/app/proguard-rules.pro`.

---

## 3. High-Definition Visual Deliverables (`docs/screenshots/`)

All 10 visual screenshots were generated from the live running application servers using headless Google Chrome (`1440x900` desktop, `390x844` mobile):

1. `01_homepage_desktop.png` (228 KB) — Homepage hero with dark theme, live stat badges, and feature highlights.
2. `02_features_desktop.png` (155 KB) — Features overview emphasizing local-first privacy and $0 budget.
3. `03_agents_desktop.png` (153 KB) — 29 Specialist AI Agents grid with category filters.
4. `04_workflows_desktop.png` (182 KB) — Interactive visual workflow automation designer.
5. `05_voice_desktop.png` (163 KB) — Hinglish Voice Mode demonstration and confirmation gate.
6. `06_download_windows_desktop.png` (168 KB) — Windows download card with verified SHA-256 checksums and setup instructions.
7. `07_download_android_desktop.png` (168 KB) — Android download card with debug APK test package and pairing guide.
8. `08_pricing_desktop.png` (183 KB) — Transparent $0/month free pricing comparison table.
9. `09_dashboard_desktop.png` (257 KB) — Local React Dashboard interface showing active agents, content pipeline, and smart memory.
10. `10_homepage_mobile.png` (97 KB) — Mobile responsive view (390x844) validating mobile navigation and responsiveness.

---

## 4. How to Download Artifacts from GitHub Actions

1. Log into your GitHub account with collaborator access to `https://github.com/NavigatorJagdish/javo-agents`.
2. Navigate to **Actions** (`https://github.com/NavigatorJagdish/javo-agents/actions`).
3. Select the target workflow run:
   - For Android test APK: **CI — Android Companion** &rarr; Download artifact `javo-agents-android-v0.1.0-alpha`.
   - For Windows installer: **CI — Windows Desktop Package** &rarr; Download artifact `javo-agents-windows-v0.1.0-alpha`.
4. Unzip the downloaded archive to extract the binaries and verify checksums against `SHA256SUMS.txt`.
