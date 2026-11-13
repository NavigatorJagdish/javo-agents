# Javo Agents v0.1.1-alpha — Owner Manual Testing Checklist
**Target Release:** `v0.1.1-alpha` (Physical Device Feedback & Real Mobile Rebuild Milestone)  
**Distribution:** Private Repository `NavigatorJagdish/javo-agents`  
**License:** MIT · 100% Free ($0.00/month default budget)  
**Platforms Covered:** Windows 10/11 x64 (Desktop) & Android 10+ API 29 (Mobile Companion)

---

## 1. Prerequisites & Release Asset Retrieval

Artifacts are hosted in the authorized private repository draft release channel:
- **Private Release Hub:** [https://github.com/NavigatorJagdish/javo-agents/releases](https://github.com/NavigatorJagdish/javo-agents/releases)
- **Draft Tag:** `v0.1.1-alpha` / `v0.1.0-alpha`
- **Release Assets:**
  - `JavoAgents-0.1.0-x64.exe` (Windows NSIS Installer)
  - `JavoAgents-Portable-0.1.0-x64.exe` (Windows Portable PE)
  - `javo-agents-android-v0.1.1-alpha-debug.apk` (Rebuilt Real Android Companion APK)
  - `SHA256SUMS.txt` (Cryptographic verification ledger)

---

## 2. Android Physical Device Testing Protocol (Real Mobile Functionality Rebuild)

### Test Case 1: Fresh Installation Baseline (Zero Fabricated Records)
*Objective: Prove that a fresh install starts with clean, truthful zero-counters rather than fictional seeded records.*
1. Install `javo-agents-android-v0.1.1-alpha-debug.apk` on a fresh physical device or clear application data in Android Settings.
2. Launch the app and proceed through onboarding to the Home dashboard.
3. **Verify Truthful Dashboard Counters:**
   - **Local Tasks:** `0`
   - **Offline Drafts:** `0`
   - **Pending Approvals:** `0`
   - **Connected Social Accounts:** `0`
   - **Zero-Cost Cap:** `$0.00`
4. **Verify Waveform Truthfulness:**
   - The central cyan/violet waveform visualizer displays **`Idle`** (NOT permanently forced into `Executing`).
   - Agent status displays: **`Phone-Only • Standby`** (or connected status when paired).
5. **Verify Empty States:**
   - Open **Approval Inbox**: displays *"No Pending Approvals. Your Supervised Autopilot queue is clear."*
   - Open **Content Studio**: displays *"No Drafts in Studio. Tap '+' to write a local draft or use Voice Mode to compose content with AI."*
   - Open **Goals**: displays *"No Growth Goals. 0 active milestones."*
   - Open **Connected Accounts**: displays *"No Connected Accounts. 0 social channels connected."*
   - Open **Notifications**: displays *"No Notifications. 0 unread alerts."*

---

### Test Case 2: Voice Mode & Native Speech Recognition (Hindi / Hinglish / English)
*Objective: Verify real speech transcription, live RMS waveform reactivity, zero prompt substitution, and direct AI fallback.*
1. Tap the **Voice Mode** tile from Home.
2. **Audio Permission:** Tap the cyan mic button. Grant the Android microphone runtime permission.
3. **Speech Recognition Test (Hindi / Hinglish):**
   - Select the **Hinglish** or **Hindi** language chip.
   - Tap the mic button. The waveform transitions to **`Listening`**.
   - Speak clearly into the microphone in Hindi or Hinglish (e.g., *"Aaj ka schedule kya hai?"* or *"Instagram ke liye ek fresh hook draft karo"*).
   - **Verify Live Streaming:**
     - Observe the live partial transcript streaming in real time inside the waveform status card: `Hearing: "..."`.
     - Observe the waveform bars dynamically scaling in amplitude with your actual voice volume.
   - Stop speaking (silence timeout triggers automatically after 1.5s, or tap the Stop button).
4. **Verify Zero Substitution:**
   - The transcribed text matches what you actually said.
   - **Crucial:** Verify the app NEVER substitutes your words with hardcoded canned text like *"Instagram reel ke liye ek fresh Hinglish hook draft karo"*.
5. **AI Routing & Response:**
   - **Case A (Windows Bridge Connected):** Command is transmitted to local PC runtime and executed by specialist agent.
   - **Case B (Direct Gemini API Configured):** When a Gemini API key is entered in Settings → AI Providers, the app makes a direct call to Gemini 1.5 Flash and returns a real multilingual AI response.
   - **Case C (Unconfigured Provider):** If neither Windows nor Gemini is set up, the assistant responds with honest diagnostic guidance and automatically saves any draft request into Content Studio.

---

### Test Case 3: Rebuilt Approval Inbox (State Machine & Action Gating)
*Objective: Ensure only genuine pending items show action buttons, while decided items display immutable status pills.*
1. In Settings, enable **Isolated Demo Mode** to populate sample approvals for testing.
2. Navigate to **Approval Inbox**.
3. **Tabs Verification:**
   - Switch between **Pending** and **Decided (History)** tabs.
4. **Pending Items:**
   - On a pending item, verify three active buttons appear: **Approve**, **Edit / Reschedule**, and **Reject**.
   - Tap **Approve**: status immediately transitions to `Approved` with a green status pill.
   - Tap **Edit / Reschedule**: dialog opens allowing content and schedule slot modification; saving transitions status to `Rescheduled`.
5. **Decided Items (No Action Buttons):**
   - Switch to the **Decided** tab.
   - Tap on the approved or rejected item.
   - **Crucial:** Verify **Approve** and **Reject** buttons are NOT present. The card displays read-only status and audit details (*"Status: Approved by Creator"*).

---

### Test Case 4: Rebuilt Content Studio (Search, Platform Filter, Full Lifecycle)
*Objective: Verify draft creation, editing, deletion, and platform filtering.*
1. Navigate to **Content Studio**.
2. **Create Draft:**
   - Tap the **'+'** Floating Action Button.
   - Enter Title: *"Behind The Scenes Reel"*, Body: *"How we built local-first autonomous agents"*, Platform: *"Instagram"*.
   - Tap **Save Offline**.
   - Verify draft appears immediately with a yellow/amber **`Queued Sync`** badge.
3. **Search & Platform Filter:**
   - Type *"Behind"* in the search bar: only the matching draft remains visible.
   - Tap the **YouTube** filter chip: draft is filtered out.
   - Tap **Instagram**: draft reappears.
4. **Edit Draft:**
   - Tap the Edit icon on the card.
   - Modify the title to *"Behind The Scenes Reel (v2)"* and save.
   - Verify updated title renders immediately.
5. **Delete Draft:**
   - Tap the Delete icon on the card.
   - Confirm deletion dialog: verify the draft is permanently removed from Room storage.

---

### Test Case 5: Safe Migration for Existing Alpha Users
*Objective: Ensure updating from v0.1.0-alpha to v0.1.1-alpha purges only legacy sample records while keeping user-created items.*
1. On an existing device with legacy sample data:
2. Install the updated APK `javo-agents-android-v0.1.1-alpha-debug.apk`.
3. Launch the app.
4. **Verify Migration:**
   - Verified legacy sample IDs (`draft-101..103`, `apr-201..203`, `goal-1..2`, `tsk-1..3`, `acc-ig..tg`, `not-1..3`) are automatically deleted.
   - Any custom drafts or tasks created by the user remain intact.
   - Migration flag `sample_migration_v1_done` prevents sample records from ever re-appearing.

---

### Test Case 6: Windows Pairing Contract (Unauthenticated Challenge Confirmation)
*Objective: Verify that a newly installed phone can confirm pairing using a 6-digit challenge code without pre-existing bearer tokens.*
1. On Windows, click **Pair New Companion Device** to generate a 6-digit challenge code (e.g., `482910`).
2. On Android, open **Pairing Screen**.
3. Enter the PC LAN URL (e.g. `http://192.168.1.50:8000`) and the 6-digit code.
4. Tap **Pair with Windows**.
5. **Verify Handshake:**
   - Android client submits `POST /devices/pair/{code}/confirm` without bearer auth.
   - Backend verifies the challenge code, persists the device record, and returns a signed device token in `PairConfirmResponse`.
   - Android securely stores the device token in Android Keystore (AES-256-GCM).
   - Home screen transitions to **`Connected to Windows`**.

---

## 3. Owner Acceptance Sign-Off Matrix

| Test Item | Verification Criteria | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Clean Baseline** | Fresh install displays 0 tasks, 0 approvals, 0 drafts | [ ] PASS | Verified Room clean state |
| **Truthful Waveform** | Waveform displays Idle when not executing; no fake running claims | [ ] PASS | Fixed forced executing bug |
| **Real Speech Input** | Android SpeechRecognizer captures Hindi/Hinglish/English voice | [ ] PASS | Native engine integration |
| **No Prompt Hijacking** | Spoken words are never replaced with canned Instagram text | [ ] PASS | Substituted prompt removed |
| **Direct AI Fallback** | Gemini API responds when Keystore key configured; honest notice if none | [ ] PASS | GeminiApiClient active |
| **Approval Inbox** | Approve/Reject only on pending items; read-only pills on decided items | [ ] PASS | Pending & Decided tabs |
| **Content Studio** | Search, platform filtering, draft editing, and deletion working | [ ] PASS | Full lifecycle active |
| **Safe Migration** | Alpha upgrade purges only exact sample IDs (`draft-101..103`) | [ ] PASS | Tested against Room |
| **Pairing Contract** | Unauthenticated 6-digit challenge code successfully pairs device | [ ] PASS | Aligned Retrofit & FastAPI |
| **Zero-Cost Policy** | 100% free-first defaults ($0.00 spend cap enforced) | [ ] PASS | MIT / Zero-cost guard active |
