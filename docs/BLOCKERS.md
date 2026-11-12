# Known Blockers & Environment Notes

| ID | Area | Description | Workaround / Next Step |
| :-: | :--- | :--- | :--- |
| **BLK-01** | `apps/android/` | `java` (JDK 17), `gradle`, and the Android SDK (API 35) are not installed on this machine, so `./gradlew testDebugUnitTest assembleDebug` / `bundleRelease` could not be executed locally. | Open `apps/android/` in Android Studio or run `.github/workflows/ci-android.yml` in GitHub Actions with JDK 17 + Android SDK 35. |
| **BLK-02** | External APIs & Credentials | No live Facebook, Instagram, YouTube OAuth client credentials, Telegram Bot token, Gemini API key, or local Ollama daemon were configured/connected during automated verification. | Connectors and AI routing are tested against local/mock implementations; configure credentials in `.env` or the Settings UI to test live APIs. |
| **BLK-03** | Release Signing & Store Review | No Windows Authenticode code-signing certificate, Android upload keystore, or Google Play Developer account access is present in this environment. The Windows NSIS and Portable `.exe` builds are unsigned. | See `docs/release/RELEASE_AND_SIGNING_GUIDE.md` and `apps/android/play-store/` for signing and submission steps. |
| **BLK-04** | GitHub Private Remote | GitHub CLI / remote repo credentials were not authenticated in this session, so no remote push to a private GitHub repository was performed. | Authenticate `gh` or add a private remote (`git remote add origin ...`) before pushing. |
