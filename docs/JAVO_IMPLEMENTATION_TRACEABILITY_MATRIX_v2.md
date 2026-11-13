# JAVO — Implementation Traceability & Owner Acceptance Matrix (v2)
**Date:** 2026-11-13  
**Branch:** fix/android-ci-and-production-hardening / PR #1  
**Baseline:** [JAVO_COMPLETE_ECOSYSTEM_MASTER_SPEC_v2.md](./JAVO_COMPLETE_ECOSYSTEM_MASTER_SPEC_v2.md)  
**Purpose:** Protect the owner from "100% ready" claims when code, simulated tests, real Android hardware, or external platform approval remain unverified.

## Status legend
- **CODE**: source implementation is present; actual user-level operation may still fail.
- **CI**: automated workflow tests completed for the exact source commit.
- **OWNER**: owner tested a named device/build and confirmed.
- **BLOCKED**: integration/credential/permission or development missing.
- **PLANNED**: explicitly selected requirement, not implemented.
- **NO DEMO SUCCESS**: no fake status counts, connected accounts, social post receipts or historical actions.

A PASS in an old workflow never transfers automatically to a newer commit. No row is OWNER PASS without evidence of actual phone operation.

| ID | Requirement | Current evidence / repo path | Engineering status | Owner acceptance |
|---|---|---|---|---|
| CORE-01 | One existing Android package and private repo | com.javo.agents; PR #1 | CODE | Not an end-to-end success |
| CORE-02 | Android-first independent onboarding | WelcomeScreen.kt, Models.kt | CODE | NOT VERIFIED |
| CORE-03 | Optional Windows pairing | PairingScreen.kt; WindowsBridgeClient.kt | CODE | NOT VERIFIED |
| CORE-04 | Optional Cloud broker/worker | Existing backend; no independent hosted setup verified | BLOCKED | NOT VERIFIED |
| CORE-05 | No fake tasks/approvals on fresh install | JavoRepositories.kt sample migration | CODE | Owner must test |
| CORE-06 | Persist selected AI provider | KeystoreManager.kt, MainViewModel.kt | CODE changed 13 Nov | New CI/device test pending |
| CORE-07 | Honest configured vs running agents | AgentTeamScreen.kt, MainViewModel.kt | CODE changed 13 Nov | New CI/device test pending |
| CORE-08 | Multi-device authenticated bidirectional sync | WindowsBridgeClient, devices.py | PARTIAL | Live paired devices not verified |
| CORE-09 | Encrypted secrets, scoped credentials | KeystoreManager.kt; backend security | CODE | Pen test required |
| CORE-10 | Live run trace, receipts, audit, user approval | Existing task/approval entities + APIs | PARTIAL | End-to-end external test blocked |
| VOICE-01 | Exact Hindi/Hinglish/English STT | VoiceRecognitionManager.kt | CODE | Owner previously saw error 11/13 |
| VOICE-02 | Bounded finalization; manual cancel | VoiceRecognitionManager.kt, VoiceModeScreen.kt | CODE | Owner has not confirmed fix |
| VOICE-03 | TTS actual audio, interrupt and focus | VoiceTtsManager.kt | CODE | Owner has not confirmed working |
| VOICE-04 | Real 10-turn context/history persisted | MainViewModel.kt session state | PARTIAL | NOT VERIFIED |
| VOICE-05 | Real independent phone AI replies | GeminiApiClient; MainViewModel | CODE | Provider/device test pending |
| VOICE-06 | User-selectable voice speed and languages | VoiceTtsManager/VoiceModeScreen | CODE | Owner device test pending |
| VOICE-07 | Wake word Hey Jarvis/Hey Javo | Feasibility required; OS policy | PLANNED | BLOCKED |
| VOICE-08 | Background + lock-screen opt-in assistant | Android OS restrictions and policy | PLANNED | BLOCKED |
| VOICE-09 | Supported app launcher/call/gallery Intents | Need scoped action tools | PLANNED/PARTIAL | BLOCKED |
| VOICE-10 | Opt-in memory edit/export/delete | History & privacy partially implemented | PARTIAL | NOT VERIFIED |
| VOICE-11 | Proactive 8am/remind/check-in cadence | WorkManager reminder only | PARTIAL | Owner test needed |
| AGENT-01 | Real master planner with bounded goals | Agent catalog and orchestration code | PARTIAL | Tool evidence incomplete |
| AGENT-02 | Actual phone specialist task execution | MobileAgentOrchestrator.kt | CODE, limited to model-generated outputs | API/device test needed |
| AGENT-03 | No arbitrary unknown agent fallback | MobileAgentOrchestrator.kt | CODE fixed 13 Nov | CI pending |
| AGENT-04 | Real per-agent activity counters | Task state vs catalog state | PARTIAL | Visual owner test pending |
| AGENT-05 | Execution logs and cancellation | Task/approval endpoints | PARTIAL | Tests needed |
| AGENT-06 | Master-agent delegation actual tools | Currently template/model routing dominates | BLOCKED | NOT VERIFIED |
| MOD-01 | Quality Inspector | Model specialist and UI; tool contract incomplete | PARTIAL | NOT VERIFIED |
| MOD-02 | Account Guardian | Credential status scaffolding | PLANNED/PARTIAL | BLOCKED |
| MOD-03 | Competitor/Niche Radar | Source adapters and provenance needed | PLANNED | BLOCKED |
| MOD-04 | Smart Approval Inbox | Approval UI, local decision APIs | PARTIAL | Live action test required |
| MOD-05 | Zero-Cost Budget Guardian | UI cap concept; metering must be proven | PARTIAL | NOT VERIFIED |
| MOD-06 | Content Recycling | Needs dedupe and provenance pipeline | PLANNED | BLOCKED |
| MOD-07 | Brand Identity Studio | Brand prompts/templates partially available | PARTIAL | NOT VERIFIED |
| MOD-08 | Weekly Strategy Board | Needs verified platform metrics | PLANNED | BLOCKED |
| MOD-09 | Offline Recovery/Backup | Room + local export; encrypted recovery/restore | PARTIAL | NOT VERIFIED |
| MOD-10 | Plugin Sandbox/Trust Score | Backend sandbox/security baseline | PARTIAL | NOT VERIFIED |
| SOCIAL-01 | Mobile Meta/Google official OAuth | ConnectedAccountsScreen currently mostly cards | BLOCKED | Requires developer setup |
| SOCIAL-02 | Facebook Page publish with live receipt | Backend connector designs exist | PARTIAL/BLOCKED | App review/scopes |
| SOCIAL-03 | Facebook Profile manual share | Separate Publisher planned/partly coded | PARTIAL | Owner validation needed |
| SOCIAL-04 | Eligible Instagram Professional publish | Platform OAuth and permissions needed | BLOCKED | NOT VERIFIED |
| SOCIAL-05 | YouTube authenticated channel management | OAuth/token exchange incomplete on Android | BLOCKED | NOT VERIFIED |
| SOCIAL-06 | Telegram bot optional command | Backend module available | PARTIAL | Real token/device test |
| SOCIAL-07 | Content creator drafts/edit/approval | ContentLibraryScreen.kt, Room | CODE | Owner test pending |
| SOCIAL-08 | Actual scheduled publish with idempotency | Needs durable clock scheduler and receipt | BLOCKED | NOT VERIFIED |
| STUDIO-01 | Android media picker + caption/draft | ContentLibraryScreen.kt | CODE | Owner test pending |
| STUDIO-02 | Video trim/captions/audio/export | Advanced media pipeline not delivered | PLANNED | BLOCKED |
| BIZ-01 | CRM/quotes/invoices/inventory | Prior 5-product master roadmap | PLANNED | BLOCKED |
| WEB-01 | Website download/verified release hashes | Next.js website, release docs | CODE | Verify each new release |
| RELEASE-01 | Private PR; no merge | Existing PR #1 | CODE | Owner to approve |
| RELEASE-02 | Real phone acceptance distinct from CI | This matrix and master doc | DOCUMENTED | Owner must test |
| RELEASE-03 | Binary provenance + signing continuity | Old v0.1.4 draft asset was overwritten by the previous PR-on-push --clobber workflow; upload gate fixed in ci-android.yml | AT RISK / CORRECTION COMMITTED | New version and complete provenance required |

## Release integrity incident (13 November 2026)

The original v0.1.4-alpha debug APK was previously listed in private Release 444076571 with SHA-256 `3ed9722b74d11f67b0183ced15c5839c3aa10c69abf7dd7eece095755c790d16`. A later query returned a different asset ID 743353257 and SHA-256 `338f608932e30fff1accf2ff846a97e379be8c7efd024db8705256869591370e` under the same filename. This demonstrates loss of asset immutability due to the prior `gh release upload --clobber` on routine PR CI runs. The workflow has been changed to **manual opt-in only, no clobber**, but older in-flight runs may still run their original workflow definitions. Do not send an old v0.1.4 checksum or claim this draft is an immutable production release. Issue a **new versioned private alpha** after all older workflows stop, all checks pass, and a fresh digest/signing test is complete.

## Immediate implementation milestones
### M0 — current source stabilization (owner blocker)
1. Ensure Android CI lint, unit and debug assembly passes on the exact latest commit.
2. Confirm provider selection persistence with regression tests and real provider responses.
3. Verify agent catalog clearly differs from active executions.
4. Provide owner-readable voice diagnostics for the real Android device.

### M1 — Companion actually conversational
1. Run 10 consecutive phone voice turns in Hindi/Hinglish including one cancelled and one interrupted turn.
2. Validate audio mode, speech errors 11/13 recovery, no stuck Listening, no duplicate command.
3. Persist opt-in conversation history and ensure no unsupported actions auto-run.
4. Test explicit selected provider including Custom AI despite a saved Gemini key.

### M2 — actual mobile work
1. Create local task; assign supported specialist; show real run ID/output/error.
2. Save/share/edit content draft, restart and verify persistence.
3. Add permission-gated Android app Intents and real reminder notification.
4. Test budget limits and signed plugin boundaries.

### M3 — real social accounts and publishing
1. Obtain official developer credentials/permissions and deploy optional confidential token exchange broker.
2. Verify account identity, scopes, expiry, disconnect/revoke and publish readiness.
3. Keep Facebook Profile manual share; no automatic post without supported permission.
4. Test scheduled Page/IG/YouTube operation with actual external receipt under owner approval.

### M4 — cross-platform and other products
Secure sync, 8GB desktop benchmarks, optional cloud/monitoring, Business, Studio and commercial tiers only after relevant readiness gates.

## Evidence policy
Every test record requires **versionCode, APK SHA-256, commit SHA, Android model/version, selected recognizer, selected provider/model, actual action, expected/actual behavior, pass/fail/blocked, notes**. Secrets, login tokens and raw personal transcripts must not be included in public logs.

**No new alpha should be declared "entire ecosystem complete" while M3/M4 are blocked.**
