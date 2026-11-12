# Google Play Permissions Justification — Javo Agents

Every permission declared in `app/src/main/AndroidManifest.xml` corresponds directly to a user-initiated feature.

## Declared Permissions

1. **`android.permission.INTERNET`** & **`android.permission.ACCESS_NETWORK_STATE`**
   - **Purpose**: Communicate with the user's explicitly paired Windows Local Runtime (`services/local-runtime`) over LAN/HTTPS and optionally call the user's configured Gemini API endpoint.
   - **Scope**: WorkManager `SyncWorker` respects `NetworkType.CONNECTED` and `requiresBatteryNotLow`.

2. **`android.permission.RECORD_AUDIO`**
   - **Purpose**: User-initiated Push-to-Talk voice commands in `VoiceModeScreen`.
   - **Runtime Request**: Requested only when the user taps the microphone button in Voice Mode. Never recorded silently in the background.

3. **`android.permission.FOREGROUND_SERVICE`** & **`android.permission.FOREGROUND_SERVICE_MICROPHONE`**
   - **Purpose**: Displays a persistent, user-controllable notification (`VoiceCaptureService`) while Push-to-Talk microphone capture is active, complying with Android 14+ foreground service type rules.
   - **Termination**: Automatically stops when the user releases/stops listening or taps "Stop" in the notification.

4. **`android.permission.CAMERA`** (`android:required="false"`)
   - **Purpose**: Optional QR code scanning on `PairingScreen` to read short-lived pairing payloads displayed by the Windows desktop dashboard.
   - **Fallback**: Users can enter pairing host/code/token manually without granting Camera permission.

5. **`android.permission.POST_NOTIFICATIONS`**
   - **Purpose**: Deliver high-priority Supervised Autopilot approval alerts (`channel_approvals`), desktop sync status (`channel_sync`), and active voice indicator (`channel_voice`).
   - **Runtime Request**: Requested politely on Android 13+ (API 33+). All core app features still work if denied.
