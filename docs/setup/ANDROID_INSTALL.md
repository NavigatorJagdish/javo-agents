# Android Companion App Installation Guide

The Javo Agents Android app (`apps/android/`) pairs with your Windows PC over your local Wi-Fi/LAN so you can approve posts, run voice commands, and draft content on the go.

## 1. Requirements

- **Android 8.0 (API 26)** or newer (Android 12–15 recommended)
- **Android Studio Ladybug / Koala** (if building from source) + JDK 17 + Android SDK 35

## 2. Building & Installing from Source

1. Open `apps/android/` in **Android Studio**.
2. Wait for Gradle Sync (`gradle/libs.versions.toml`) to finish.
3. Connect your Android phone via USB (with USB Debugging enabled) or start an Android Emulator.
4. Click **Run (`app`)** or execute:
   ```bash
   cd apps/android
   ./gradlew assembleDebug
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

## 3. Pairing with Windows Local Runtime

1. Ensure your Windows PC and Android phone are on the **same Wi-Fi network**.
2. On Windows Dashboard, go to **Security → Pair Device** to generate a short-lived QR code & pairing token.
3. On Android, open **Pairing Screen**, grant Camera permission, and scan the QR code (or enter your PC's LAN IP + pairing code).
4. Your pairing secret is encrypted in **Android Keystore** (`KeystoreManager.kt`).
5. You can revoke any paired phone instantly from **Windows Dashboard → Security → Trusted Devices**.
