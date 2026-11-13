# Javo Agents v0.1.0-alpha — Owner Manual Testing Checklist
**Target Release:** `v0.1.0-alpha` (Private Alpha Milestone)  
**Distribution:** Private Repository `NavigatorJagdish/javo-agents`  
**License:** MIT · 100% Free ($0.00/month default budget)  
**Platforms Covered:** Windows 10/11 x64 (Desktop) & Android 10+ API 29 (Mobile Companion)

---

## 1. Prerequisites & Private Alpha Package Retrieval

Because this repository is strictly private, build artifacts cannot be accessed by unauthenticated web browsers.

### Step 1.1: Ensure GitHub Authentication
1. Open your web browser and ensure you are logged into your GitHub account (`NavigatorJagdish` or an authorized repository collaborator).
2. Navigate to the **Private Release Hub**:  
   [https://github.com/NavigatorJagdish/javo-agents/releases](https://github.com/NavigatorJagdish/javo-agents/releases)
3. Locate draft release **`v0.1.0-alpha`** (Release ID `443379038`).

### Step 1.2: Download Release Assets
Download the following tested binaries:
- `JavoAgents-0.1.0-x64.exe` (Windows NSIS Installer, ~78 MB)
- `JavoAgents-Portable-0.1.0-x64.exe` (Windows Portable PE, ~77.8 MB)
- `javo-agents-android-v0.1.0-alpha-debug.apk` (Android Test APK, ~18.2 MB)
- `SHA256SUMS.txt` (Cryptographic verification ledger)

### Step 1.3: Cryptographic Checksum Verification
Open Windows PowerShell in the download directory and run:

```powershell
Get-FileHash .\JavoAgents-0.1.0-x64.exe -Algorithm SHA256
Get-FileHash .\JavoAgents-Portable-0.1.0-x64.exe -Algorithm SHA256
Get-FileHash .\javo-agents-android-v0.1.0-alpha-debug.apk -Algorithm SHA256
```

**Expected Results:**
- `JavoAgents-0.1.0-x64.exe`: `5e4d760243703824f911c5c21109d4bed101e9ec7a4896c5c4e693ddc4e2ecac`
- `JavoAgents-Portable-0.1.0-x64.exe`: `2adad28ad367402b9ba060445eb686017b5359877c83985a7a5e659d603686ce`
- `javo-agents-android-v0.1.0-alpha-debug.apk`: `a8f58a573e0a3fe868f917a42790d74573194947999a4cc93dd64719900fe1a8`

*(If hashes do not match, do not proceed; re-download directly from GitHub).*

---

## 2. Windows Desktop Testing Protocol

### Scenario A: Clean Machine Test (No Python installed / PATH unset)
*Objective: Prove that the desktop application fails gracefully with honest diagnostics rather than crashing or showing deceptive online indicators.*

1. **Launch:** Double-click `JavoAgents-Portable-0.1.0-x64.exe` on a PC or Windows Sandbox where Python 3.10+ is absent.
2. **SmartScreen Prompt:** When Windows Defender SmartScreen appears ("Windows protected your PC"):
   - Click **"More info"**
   - Click **"Run anyway"**  
   *(Expected for unsigned alpha binaries)*
3. **Observation:**
   - The desktop shell window opens with the dark navy UI theme (`#0B1026`).
   - The sidebar status pill shows: **`Offline (127.0.0.1:8000)`** in red.
   - An amber notification banner appears:
     > *"Local Runtime Offline: Cannot connect to Javo Agent backend at http://127.0.0.1:8000. Ensure Python 3.10+ is installed and the background service is running."*
   - Clicking *"Install Python 3.10+"* opens the official Python download page in the default browser.
   - The app remains responsive and does not freeze or crash.

---

### Scenario B: Standard Operation (Python 3.10+ installed)
*Objective: Verify full desktop orchestration, system tray integration, and local loopback binding.*

1. **Launch:** Launch `JavoAgents-0.1.0-x64.exe` on your standard development/testing machine.
2. **System Tray:** Check the Windows taskbar notification area (near clock):
   - A Javo Agents tray icon appears.
   - Right-click the tray icon to verify menu items:
     - `Javo Agents (Port 8000)` (Header)
     - `Open Dashboard`
     - `Pause Autopilot` / `Resume Autopilot`
     - `Emergency Stop (Kill Switch)`
     - `Quit Javo Agents`
3. **Dashboard Health:**
   - The window displays the React dashboard.
   - Sidebar status displays: **`Healthy (127.0.0.1:8000)`** in green.
   - Hardware detection card displays your machine's CPU cores, total RAM, and recommended local AI model tier (e.g. `llama3.2:3b` for 8GB RAM).

---

### Scenario C: Subsystem & Feature Smoke Tests
Perform these 5 quick actions in the dashboard:

1. **Goal Creation:**
   - Navigate to **Goals** in the left sidebar.
   - Click **"Create New Goal"**.
   - Enter title: *"Test Alpha Campaign"* and submit.
   - **Expected:** Goal appears immediately in the active goals list with `0.0%` progress.
2. **Content Factory Pipeline:**
   - Create a test folder on your PC (e.g. `C:\javo_test`) containing one image (`sample.jpg`) or text note (`test.txt`).
   - Navigate to **Content Factory** (or trigger scan via API `/content/pipeline/run`).
   - **Expected:** Discovers file, classifies MIME type, generates localized draft caption and hashtags (`#JavoAgents`), and creates a `PENDING` schedule.
3. **Approval Flow:**
   - Go to **Approval Inbox**.
   - Review the queued draft schedule.
   - Click **"Approve"**.
   - **Expected:** Schedule status transitions from `PENDING` to `APPROVED`. In simulated mode, logs record simulated dispatch without charging or posting live.
4. **Voice Interface:**
   - Navigate to **Voice**.
   - Type or speak: *"Schedule a new reel for tomorrow morning"*.
   - **Expected:** Routed agent displays `master_orchestrator`, intent is classified, and text-to-speech audio feedback is generated.
5. **Emergency Stop (Kill Switch):**
   - Click the red **Emergency Stop** button in the dashboard or choose it from the system tray menu.
   - **Expected:**
     - Windows notification pops up: *"EMERGENCY STOP ACTIVATED: All agent actions and publishes halted."*
     - Global autopilot state displays *"Emergency stop active"*.
     - Click **"Resume Autopilot"** in the tray; verify normal operation resumes cleanly.

---

## 3. Android Mobile Companion Testing Protocol

### Scenario A: Android Emulator Verification (AVD)
1. Start an Android Virtual Device running Android 10+ (API 29 to 35).
2. Install the debug APK via Android CLI or adb:
   ```bash
   adb install javo-agents-android-v0.1.0-alpha-debug.apk
   ```
3. Launch **Javo Agents** from the app launcher.
4. **Permissions Check:**
   - Microphone permission dialog appears upon entering Voice mode.
   - Notification permission dialog appears (Android 13+).
   - Camera permission dialog appears upon tapping QR Scan.
5. **Pairing with Emulator:**
   - On emulator, the host machine's loopback address is accessible via `http://10.0.2.2:8000`.
   - In pairing screen, enter host URL `http://10.0.2.2:8000` and enter the 6-character desktop pairing code.
   - **Expected:** Pairing handshake completes, token is encrypted into Android Keystore, and companion home screen displays desktop connection status.

---

### Scenario B: Physical Android Device Testing
1. **Transfer APK:** Sideload `javo-agents-android-v0.1.0-alpha-debug.apk` to your Android phone via USB cable or local file transfer.
2. **Installation:** Tap the APK in your phone's File Manager. When prompted, toggle on *"Allow from this source"* and complete installation.
3. **Wi-Fi Pairing:**
   - Ensure your phone and Windows PC are connected to the **same local Wi-Fi router**.
   - In the Windows desktop app, open **Devices** -> **Pair New Companion** to reveal the LAN QR code.
   - Open Javo Agents on your phone, tap **Scan QR Code**, and point your camera at the PC screen.
   - **Expected:** Phone validates the LAN TLS/HTTP payload, exchanges tokens, and connects within 2 seconds.
4. **Offline Draft Cache Test:**
   - On your phone, turn **Airplane Mode ON** (disable Wi-Fi and mobile data).
   - Create a new content draft in Javo Agents: Title *"Offline Reel"*, Caption *"Created with zero internet"*.
   - Save the draft.
   - **Expected:** Draft displays with an orange *"Pending Sync"* badge.
   - Turn **Airplane Mode OFF** (reconnect Wi-Fi).
   - **Expected:** Background sync detects desktop connectivity, uploads the draft, and status changes to green *"Synced"*.

---

## 4. Website Local Preview & Documentation Testing

### Running the Website Preview Locally
1. In terminal, navigate to the repo root and run:
   ```powershell
   cd d:\antigravityproject\javo-agents
   npx serve apps/website/out -p 3000
   ```
2. Open your browser to [http://127.0.0.1:3000](http://127.0.0.1:3000).
3. **Verification Points:**
   - **Download Page (`/download`):** Verify Windows Installer, Portable, and Android APK cards show exact matching SHA-256 digests.
   - **Download Links:** Clicking download buttons points directly to the verified release asset URLs.
   - **Disclaimers:** Verify private alpha notice, SmartScreen explanation, and Python 3.10+ requirement disclosures are prominent.
   - **Agent Roster (`/agents`):** Browse all 29 specialist agents and Master Orchestrator specs.
   - **Theme Toggle:** Switch between Dark and Light mode (top right navigation bar).

---

## 5. Owner Acceptance Sign-Off Matrix

Use this checklist during manual validation:

| Test Area | Item Description | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Integrity** | SHA-256 matches `5e4d76...` for Windows Installer | [ ] PASS | Verified against storage |
| **Integrity** | SHA-256 matches `2adad2...` for Windows Portable | [ ] PASS | Verified against storage |
| **Integrity** | SHA-256 matches `a8f58a...` for Android Debug APK | [ ] PASS | Verified against storage |
| **Windows** | SmartScreen prompt appears and allows "Run anyway" | [ ] PASS | Expected for unsigned alpha |
| **Windows** | Clean machine shows red Offline banner with Python link | [ ] PASS | Tested in desktop shell |
| **Windows** | Standard launch connects to `127.0.0.1:8000` | [ ] PASS | Verified in smoke tests |
| **Windows** | System tray icon allows Pause, Resume, Emergency Stop | [ ] PASS | Authenticated with owner token |
| **Windows** | Goals, Content Factory, and Voice respond correctly | [ ] PASS | All 8 subsystems verified |
| **Android** | Debug APK installs on Android 10+ (API 29+) | [ ] PASS | Multidex + Compose verified |
| **Android** | Permissions (Microphone, Camera, Notifications) handled | [ ] PASS | Declared in Manifest |
| **Android** | Offline draft stays queued and syncs when online | [ ] PASS | Verified in Room repository |
| **Android** | LAN QR code pairing succeeds over Wi-Fi | [ ] PASS | AES-GCM Keystore token |
| **Website** | 24 pages render cleanly without broken links | [ ] PASS | Static export verified |
| **Website** | Clear $0.00/month free-first disclosures | [ ] PASS | Highlighted across site |
