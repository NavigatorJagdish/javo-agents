# JAVO — COMPLETE ECOSYSTEM MASTER SPECIFICATION
## Requirements Recovery · Product Contract · Engineering Blueprint · Test Gates
**Version:** 2.0 (reconciled)  
**Date:** 13 November 2026  
**Status:** APPROVED REQUIREMENTS BASELINE / NOT A CLAIM OF IMPLEMENTATION  
**Source of truth:** Previous Javo conversations, 12 November 2026 Five-Product Master Blueprint, and owner Android field testing through v0.1.4-alpha.  
**Current implementation:** private repository NavigatorJagdish/javo-agents; existing Android applicationId com.javo.agents; Android, Windows, Website, FastAPI local runtime.  
**Privacy:** Internal product design. Do not put keys, social access tokens, passwords, actual contact data or personal speech transcripts in this document.

> **Product promise**: Javo is a Hindi/Hinglish-first, natural conversational AI team that completes authorized work through a Master Orchestrator, independent-capable mobile assistants, specialist workers, and supervised automation. Product copy must not claim successful automation unless a real verified result exists.

## 0. Immutable owner decisions

1. **One Javo Agents ecosystem.** Upgrade the existing Android app/repo, not a replacement APK/application ID or unrelated repo. Shared Core can also support separate commercial product surfaces.
2. **Android standalone first.** No Windows pairing, Python runtime, laptop, or always-on PC required for basic onboarding, text/voice AI with a configured provider, local tasks, drafts, notes, reminders and supported local actions. Windows/cloud only extend capabilities.
3. **Natural assistant, not a static dashboard.** Speak Hindi naturally, understand Hinglish and English, reply audibly and promptly, remember opt-in preferences, perform requested supported actions. The assistant is the main home entry.
4. **Supervised autonomy.** Master Agent + specialist workers + proactive monitoring; a goal can be planned, assigned, resumed, cancelled and reported. Public posts, messages, spending, deletions, calls and privileged phone actions have scoped permissions and confirmation/approval.
5. **Free-first and local-first.** Prefer device/Windows models where useful; optional BYOK Google Gemini/custom AI APIs; report quota and cost. Free usage is not unlimited; $0.00 is a chosen budget cap, not a fabricated billing guarantee.
6. **Phone and midrange Windows performance.** Android target includes a consumer Realme-class Android 16 phone; Windows target includes an 8 GB RAM laptop. Low storage, battery, heat and slow connectivity must be handled.
7. **Consistent Javo brand.** Existing logo/identity; midnight navy, electric cyan, violet, disciplined spacing, premium futuristic but calm UX, accessible contrast. Hindi/Hinglish-first UI with English mode.
8. **Real data only.** Fresh install shows 0 actual tasks/drafts/approvals/connections. All examples are opt-in and clearly labelled DEMO. Never substitute canned speech commands, fake agent activity, unverified analytics or fabricated "posted/synced/queued" messages.
9. **Private repository and owner gate.** Keep NavigatorJagdish/javo-agents private, use existing PR #1/working branch unless the owner requests otherwise; no merge or public release without approval. Versioned APK assets, signed upgrade strategy, exact SHA-256, CI evidence and real-device acceptance reports.
10. **Official integrations.** No password scraping, unauthorized bots, fake followers/views, fake analytics, cookie harvesting or bypass of platform permissions. Facebook Profile publishing is manual-share/export unless an authorized API expressly permits the requested action; Pages/Instagram Professional/YouTube require eligible scopes and OAuth.
11. **Distinct product lines.** The prior five-product company plan is Javo Social AI, Javo Agents Platform, Javo Business, Javo Voice/Jarvis, Javo Studio, supported by common Javo Core and future Javo Cloud. One shared architecture does not mean all future premium products are shipped inside the first alpha. The separately discussed Javo Social Connector/Publisher is not silently merged or deleted.
12. **Truthful readiness.** Compiling, green CI, installed APK, emulator acceptance, real phone acceptance and live external account acceptance are different statuses. A manual test not performed by the owner stays BLOCKED/NOT VERIFIED.

## 1. North-star end-user experience

Home opens into **Javo Companion**: large live orb/waveform, one clear Talk button, persistent keyboard input, concise conversation transcript, model/connection health, ability to switch agents or see running work. Secondary Work, Studio, Accounts and More tools are reachable but do not obscure the conversation.

Example conversation:
- Owner: "Javo, aaj mere Facebook Page ke liye paanch posts bana do aur approvals mein rakho."
- Javo: recognizes the exact words; uses configured AI; creates five distinct persisted editable drafts; shows five records with source/model; asks before publishing.
- Owner: "Kal 8 baje mujhe yaad dilana." Javo shows local date/time and permission preview; creates a real reminder and confirms only after scheduler persistence.
- Owner: "YouTube kholo." Uses supported Android Intent; if app missing, asks permission and opens supported web fallback; never simulates opening.
- Owner: "Mere video ka smooth edit karke Instagram ke liye banao." Imports media through system picker, estimates compatible processing, runs an available local editor or clearly offers optional Windows/cloud rendering; never silently crops.
- Owner: "Mujhe ek ghante baad yaad dilana agar main wapas na aaun." Opt-in user-selected re-engagement notification subject to OS/quiet hours; not covert tracking or guaranteed wake calls.

Success measured by **verified completed user tasks and satisfaction**, not number of "agents online" badges.

## 2. Shared Javo Core and platform boundaries

**Javo Core**: identity/workspaces, consent, capability registry, AI-provider gateway, agent/task state machine, tool registry, secure credentials, approval policy, audit/event log, notifications/reminders, knowledge/memory, source provenance, file/media references, usage budgets, sync, monitoring, export/deletion.

**Android**: Kotlin/Jetpack Compose, Room, Android Keystore, WorkManager, SpeechRecognizer, TTS, Photo Picker, permitted Intents and notifications; independent local state plus BYOK network AI. Must not require Windows server for ordinary use.

**Windows**: Electron/React shell, packaged local Python FastAPI runtime, optional Ollama, heavier FFmpeg/workflows, authenticated device pairing, desktop tools. Must handle missing Python/runtime honestly, 8 GB RAM and PC sleeping/offline.

**Website**: public brand/docs/downloads and, where implemented, authenticated workspace dashboard. Download pages show correct releases, signing/test status, SHA-256 and clear private collaborator restrictions.

**Optional cloud/VPS**: narrowly scoped OAuth broker, encrypted token exchange, webhook handling, reliable scheduling/monitoring and cross-device synchronization when explicitly enabled. A phone is not a reliable always-on server, so 24/7 publishing/monitoring must not be promised without this infrastructure.

**Separate product modules**: Social AI, Business, Voice/Jarvis and Studio share Javo Core and common design tokens but have bounded APIs, permissions and release maturity.

## 3. AI providers and routing (MUST / P0)

**Provider screen must be visible from Home, Voice, Settings and onboarding.** Supported first: BYOK Gemini with real model listing/versioning; validated custom OpenAI-compatible endpoint; optional authenticated Windows Ollama. Later adapters only after actual verification. Configured, connected, responding, quota exhausted, disconnected and unsupported are separate states.

Routing must honor explicit **selected provider**, not silently take whichever key exists. Never route phone-only chat to Windows without user selection. When provider fails show error class, retry and alternative; do not submit an action to another provider if data/privacy permission differs.

Provider state: selectedProviderId, modelId, endpointURL, credentialRef, capabilities, pricing disclosure, healthLastChecked, quota/cost guard, user consent. Key masked in UI and sanitized in log; never embed platform-wide secrets in Android APK. Provider tests must use a real request and label exactly what they tested.

AI gateway: structured message roles, multi-turn context, output streaming if supported, structured tool-call proposals (never execute directly), response cancellation, latency and token-budget reports, retry cap, source references for retrieved facts.

## 4. Voice / Jarvis experience (MUST / P0)

**User goal:** natural, expressive Hindi/Hinglish/English voice that feels like a conversation, not the slow type->TTS robot. Optional warm/playful persona; avoid fake human identity and respect privacy.

Voice state machine: IDLE > CONNECTING > LISTENING > FINALIZING > THINKING > RESPONDING > SPEAKING > IDLE; plus ERROR, CANCELLED. Real OS mic permission, visible indicators, exact transcript, end-of-speech detector, partial/final reconciliation, bounded finalization and explicit tap-to-cancel.

Handle Android SpeechRecognizer errors 11 service disconnected, 13 language unavailable, 12 language unsupported, recognizer busy/network/audio/permission. Before choosing on-device recognize language availability, or fallback to supported system recognition with informed consent. Do not automatically submit a speculative partial as irreversible command; display confirmation on low-confidence or partial results.

Text-to-Speech: installed supported voices, language check, correct audio focus, onStart/onDone/onError, speed, silence and interruption; distinguish "response text generated" from "actually spoken." Hands-free mode user initiated and session bounded; after speaking, reopen mic only when permitted and after echo protection. No hidden permanent recording.

**Wake word aspiration:** user has asked "Hey Jarvis"; later project references "Hey Javo". Make phrase user-configurable where feasible. Always-on/background/locked-screen listening is an advanced opt-in feasibility task subject to battery, policy and OS restrictions—not part of guaranteed first release. Never bypass lock.

**Memory:** locally encrypted conversation history; controls for save/recall/edit/export/delete and explicit retention. Optional daily preferences and proactive reminders; never invent personal memories.

**Phone commands:** approved Intent-based launch apps (YouTube, Gallery/Picker, Instagram, supported dialer); draft/upload flows through official APIs/chooser. Confirm calls/posts; never claim unrestricted tap/type control or abuse accessibility.

## 5. Master Orchestrator and autonomous agent team (MUST / P0, scaling P1+)

**Agent != prompt template.** A truly available agent must declare manifest, actual tool implementation, input/output schema, authorization, execution environment (Android/Windows/cloud), budget, failure paths and tests. Catalog can contain 29 proposed specialists; only tested executable agents count as RUNNABLE; only currently running jobs count as RUNNING.

Shared execution: user intent > classify > plan bounded subtasks > capability & cost check > permission grants > tool execution > verification evidence > approval if external > persist result + trace > audible/visual summary.

Jobs have durable IDs and states CREATED, PLANNED, BLOCKED_CAPABILITY, WAITING_PERMISSION, WAITING_APPROVAL, QUEUED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED. Every state transition is validated. No duplicate retries, no fake completed tasks, no unbounded self-recursion.

Initial mobile-capable agents: General Javo, Master Coordinator, Task Planner, Caption Writer, Script Writer, Hashtag Assistant, Brand Tone Editor, Translation, Research with attributed sources, Content Quality Checker, Local Reminder/Notes, Media Organizer and Analytics Interpreter only for verified account metrics.

Windows/cloud extended specialists: Coding, App Builder, Website Builder, Media Renderer, External Monitoring, DevOps, Workspace Sync, Social Publishing, Security Audit, QA, specialized growth workflows, optional integrations. Agent status and permissions reflect execution host.

**Ten chosen differentiators (owner explicitly selected 10/10):**
1. Quality Inspector: style, factual/duplicate/copyright-risk checks, user override and revision evidence.
2. Account Guardian: scope/token expiry, suspicious access, revoke, safety alerts; never claim real-time provider security monitoring absent permissions.
3. Competitor/Niche Radar: approved/public sources, timestamps, signal confidence, no prohibited scraping.
4. Smart Approval Inbox: clear preview/diff, action digest, expiry, one-time approval, edit/reject and immutable audit.
5. Zero-Cost Budget Guardian: explicit $0 initial cap, per-model usage metering, quota handling, fail-closed spending.
6. Content Recycling: originality check, new variant suggestions, duplicate/spam guard.
7. Brand Identity Studio: brand kit, tone, audience, templates, forbidden claims and per-client separation.
8. Weekly Strategy Board: weekly decisions, next actions, metric provenance; no fabricated performance.
9. Offline Recovery/Backup: reliable local drafts, export, encrypted optional backup, restore dry run, conflict and migration tests.
10. Plugin Sandbox/Trust Score: signed/versioned manifests, permissions, static checks, isolated execution, rollback and no arbitrary untrusted code by default.

## 6. Tasks, workflows, reminders and proactivity

Create/modify/delete tasks with title, voice-origin transcript, owner, assigned agent, priority, due timestamp/timezone, status, action log, output artifacts and retry policy. Preserve data across restart/version update and offline use.

Goal persistence: natural-language outcome > measurable milestones > dependency graph > bounded budget > periodic review; resumable when explicitly enabled. Supervised Autopilot always shows action plan and can be paused or emergency-stopped.

Automations: one-off and recurring calendar, content planning, approvals, digest and follow-up triggers. Android WorkManager/AlarmManager only for OS-compatible intervals/permissions; if phone is off, do not say unattended post definitely occurred. Optional secure cloud scheduler only after user enables it.

Proactive behaviors requested: daily wake-up/reminder around 8:00 AM when configured; opt-in check-in after approximately 1–1.5 hours of inactivity; alert when tasks fail, replies arrive, approvals await action, scheduled content is due. Quiet hours, frequency caps and disable controls are mandatory.

Run console: tool traces, evidence, actual outputs, latency, errors, cancellation, audit. Emergency Stop must stop real local jobs and report remote stop separately; no false remote acknowledgement.

## 7. Social accounts and authorized publishing

**Scope:** Facebook Pages; eligible Instagram Professional accounts; YouTube channels; Telegram bot where permitted. Owner also wants Facebook Profile posting, but manual share/export is the supported default unless platform expressly provides legitimate permission. Social account placeholders are not connections.

Native account flow: platform prerequisite > launch system browser/official SDK > OAuth/PKCE where applicable > verify state and redirect > secure code/token exchange (hosted broker when confidential client secret required) > authorized user/account identity fetch > permissions listing > persist encrypted credential reference > expiry/reconnect/revoke. Never request raw account passwords.

Connected accounts screen has distinct CONNECTED, ACTION_REQUIRED, EXPIRED, UNAVAILABLE, DISCONNECTED. Test API read permission separately from publish permission. Manual entry of a handle cannot produce CONNECTED.

Publishing: drafts -> review -> approval -> scheduled (only when actual scheduler has job ID) -> dispatching -> external provider accepted/reconciled -> published. Retry/idempotency key and duplicate media safeguards. For Facebook profile allow manual-share flows. Platform API permissions, app-review, rate limits, policy and eligible account types gate capabilities.

**Separate Javo Social Connector / Publisher:** user previously asked for standalone Android publishing tool separate from Agents because the laptop is not always on. Maintain it as separate app/product when it exists; reuse Javo Core connector contracts as optional integration, not duplicate source credentials or silently absorb branding.

Creator examples: 100 distinct Facebook comics batches (10 separate images, never collages), queue with scheduled/approved progression, never claim auto-publishing without a real authorized Page/IG integration. Human/personal Facebook Profile use chooser/manual posting. Multi-account brands, captions, tags, calendars and copyright attribution.

## 8. Content Studio and media creation

Baseline: project library, photo/video import, templates, editable captions/scripts/hashtags, image and video previews, text revisions, language and voice styling, drafts, platform exports, multi-post batches and approval. Do not silently replace requested moving visuals with stills. Each requested comic/image is separate.

Advanced: timeline trim/cut, subtitles and SRT, 9:16/1:1/16:9 no-crop modes, audio enhancement and multi-character voice where licensed, speed/smoothing, clean exports, content recycling and image/video AI transformations only where models/tools truly support them. Android lightweight; heavy render on Windows/cloud optionally; preserve source media rights and provenance.

Truthful statuses LOCAL_DRAFT, NEEDS_REVIEW, APPROVED, QUEUED, SYNCING, SCHEDULED, PUBLISHING, PUBLISHED, FAILED, MANUAL_EXPORT, SIMULATED. SIMULATED never appears as PUBLISHED.

## 9. Other Javo product domains (strategic scope)

**Javo Social AI:** brand profile; idea board; caption generation; draft editor; calendar; export; approvals; OAuth; scheduling; analytics; experiments; multi-brand agency; content recycling; weekly report.

**Javo Agents Platform:** agent catalog; task inbox; planner; workflow builder; tool registry; run console; approval inbox; long-term memory; scheduling; notification actions; cost guard; secrets; sandbox; knowledge base; run evaluation and optionally audited skill marketplace.

**Javo Business:** CRM/contacts, lead stages, quotes/invoice/PDF, inventory, opt-in follow-up drafts, customer timeline, roles, import/export, records and optional customer portal. No spam/outreach after opt-out; no implicit auto-charge.

**Javo Voice/Jarvis:** voice assistant capabilities and phone controls above; future opt-in wake word/background/lock features.

**Javo Studio:** editing, media ingest, captions, templates, local exports and optional expensive AI/cloud media features.

**Javo Cloud:** shared infrastructure and optional later paid/hosted offering, not a compulsory dependency for Android-only baseline.

**Javo ReVanced:** a separate branding/patching ecosystem with its own Android package/risks. Do not combine it into Javo Agents simply because both use the "Javo" brand.

## 10. Screen inventory and UX contract

Android onboarding: welcome > Android Standalone (default) > optional language & permissions > AI provider test or Skip > first conversation; Windows pairing advanced/optional. User can recover configuration from Voice and Home.

Android bottom navigation proposed: **Javo** (chat-first), **Work** (agents/tasks), **Studio**, **Inbox**, **More** (accounts/settings/analytics). Give social connection a visible Home shortcut. Voice mode should feel like one continuous conversational space, with persistent text input, transcript bubble, microphone orb, audio toggle, speaking/stop control and explicit actions.

Desktop: sidebar Workspaces, Javo Chat, Agent Runs, Content Studio, Social, Approvals, Monitoring, Security, Settings; performance-conscious on 8GB.

Web: product overview, transparent pricing, docs, private alpha/download/release notes, verified compatibility and support. Paid user accounts/workspaces only when a genuine backend exists.

Every screen: zero/empty, loading, real connected, offline, permission needed, quota exhausted, error, retry, cancelled, success proven. Avoid 10+ decorative cards before the primary action. Accessibility: 48dp taps, sufficient contrast, dynamic type, TalkBack, keyboard/input navigation.

## 11. Data and API model

Canonical entities: Workspace, User, Membership, Device, ProviderConfig, SecretReference, AgentDefinition, AgentCapability, Task, Run, RunStep, Workflow, Trigger, Approval, ToolGrant, Notification, MemoryEntry, BrandProfile, Draft, MediaAsset, SocialConnection, PublishJob, ExternalReceipt, AnalyticsMetric, CostLedger, BackupManifest and AuditEvent.

Every tenant object: stable ID, workspace, owner/creator, version, created/updated times, provenance, permissions, lifecycle status. Offline mobile UUIDs; only mark SYNCED after durable authenticated ack and verification. No hardcoded "14 active agents".

Contract: versioned /v1 endpoints, JWT/OAuth where appropriate, request_id, error codes, idempotency keys, audit trace, authenticated ownership checks; provider OAuth scopes/expiry; secure webhooks signature and replay guard; publish acceptance receipts.

Device pairing only via owner-initiated expiring challenge; verify authentication rather than /health as proof of pairing. Transport security, token rotation and revocation, no secrets in logs.

## 12. Security, privacy, user approval

Use least-privilege tools, explicit tool manifests, scoped consents and expiring grants. Sandbox plugins; protect data against prompt injection from external content. Permission-sensitive phone actions use supported APIs; never unlock phone, bypass permissions, secretly record, or silently manipulate others' apps.

Publishing, spending, changing credentials, mass messaging, deletion, calling and public account modifications require explicit preview/authorization. Analytics display sources, freshness and limitations. Workspace isolation, rate limits, backups, secret scanning, Android signing/version migration, incident response and responsible data retention.

## 13. Budgets, scale and commercialization

Initial free-first aspiration: no mandatory recurring platform cost for local Android drafts and BYOK use; user pays network/data and any provider usage. No promise of unlimited free inference. Initial optional VPS previously considered around **₹500–₹1,000/month monthly billing** for limited scheduling/agents, subject to current pricing and performance; 8GB Windows local-first benchmark. Run 1–2 light workers on low-spec hosting rather than falsely claiming unrestricted parallel heavy agents.

Future company roadmap: Javo Social AI earliest product to validate real revenue; shared Agents Core; Business, Voice and Studio add-ons as demand and cost justify. Previous indicative (not approved) plan hypotheses: Free ₹0, Creator ₹299/month, Pro ₹799/month, Agency ₹2,499/month; test with users, never promise profit.

## 14. Release disciplines

Existing repository and package: NavigatorJagdish/javo-agents, com.javo.agents; private PR #1 until owner approval. Versioned release APK/AAB, debug vs signed production separation, signing continuity, binary SHA-256 and matching site manifest, release provenance, changelog and rollback.

CI passes do not equal hardware passes. Required acceptance matrix reports CODE REVIEW, UNIT, API/CONTRACT, EMULATOR, REAL DEVICE, REAL ACCOUNT/OAUTH, SECURITY and OWNER ACCEPTANCE independently.

Do not publish social content, merge PR, open-source the repository, push paid launch or grant production credentials without owner approval.

## 15. Priority build waves / dependency graph

**Wave 0: truth and recovery** — freeze source/release head; backup and migration; requirements trace; remove all fake metrics/states; fix crash and permission bugs; reproduce owner phone failures.

**Wave 1: assistant that really talks** — clean Android-only onboarding; choose/test provider; selected-provider routing; reliable STT (errors 11/13 + stalled finalization); natural TTS with visual speaking state; persistent multi-turn chat; cancellation; microphone diagnostics. Owner must finish 10 consecutive spoken turns on phone without forced restarts.

**Wave 2: real mobile work** — task CRUD/execution trace; specialist capability gating; persistent notes/reminders; content draft generation and editing; quality inspector; meaningful approvals; offline recovery; cost guard.

**Wave 3: social authorization** — hosted OAuth broker when needed, official Facebook Page/IG Professional/YouTube eligible connectivity; manual profile share; verified publishing receipt; approval/duplicate safeguards; account guardian.

**Wave 4: optional Windows/Cloud parity** — secure pairing and bidirectional sync; cloud scheduler; proactive monitoring; media processing; telemetry and recovery.

**Wave 5: company-wide products** — Business CRM, deeper Studio edit suite, paid workspaces/billing and plugin marketplace, separately gated.

No arbitrary "100% complete" claim before external prerequisites and owner validation.

## 16. Master acceptance contract (test IDs)

A01 Clean install => empty real data, no mandatory PC.
A02 First chat => explicit provider setup or genuine provider response.
A03 Android STT Hindi/Hinglish/English => exact transcript; failures actionable.
A04 Voice stops/finalizes reliably; timeout never fabricates content.
A05 TTS genuinely speaks real answer; interruption and audio-focus safe.
A06 Ten consecutive voice turns with no stuck loop and bounded latency.
A07 Selected AI provider is honored; failures truthful; secrets redacted.
A08 Notes/tasks/reminders persist after restart and OS constraints explained.
A09 Mobile agents execute actual tools with output and trace; others BLOCKED.
A10 Master planning delegates bounded subtasks with consent.
A11 Approved content creates actual revisioned drafts and survives reinstall upgrade.
A12 Approval state transitions enforce one-time authorization.
A13 Social account displays CONNECTED only after real OAuth identity verified.
A14 Facebook Profile uses manual share; Page/IG publish only with actual scope.
A15 Scheduled publish has real scheduler job and external receipt.
A16 Cloud/Windows optional; mobile remains useful when offline/unpaired.
A17 Sync idempotent and authenticated; data migrates intact; no false receipts.
A18 Emergency stop reports local and remote outcomes separately.
A19 Budget hard caps, provider quotas and plugin sandbox negative tests pass.
A20 UI accessible; phone settings visible; no decorative "Active 29" fiction.
A21 Backup/restore verified; user can export/delete memory and disconnect.
A22 Code commit, APK digest, signing and source provenance reconciled.
A23 Physical device tests actually executed by owner/hardware and labelled accordingly.
A24 User acceptance confirms usefulness, not merely compilability.

## 17. Current implementation gap snapshot (13 Nov 2026; source inspected)

Status is observational and may evolve with new commits:
- AVAILABLE IN CODE: Android standalone mode selector, VoiceRecognitionManager, VoiceTtsManager, basic text chat and Gemini BYOK, Room local drafts/tasks, basic mobile orchestrator, WorkManager reminder, Windows bridge, website/download and CI workflows.
- INCOMPLETE/UNVERIFIED: compelling natural voice UX on real device, memory-driven multi-turn assistant, reliable all-day background/wake word, social OAuth flows, true running agent status, configurable selected provider routing, owner-approved real platform publishing, durable cross-device service orchestration, unified product packaging.
- UNDELIVERED strategic scope: full Business/Studio product suites, billing, multi-tenant cloud, public app-store signed release.
- Recent owner findings: hardcoded demo tasks and substituted speech commands were removed; errors 11/13 and "Listening forever" led to successive v0.1.2/v0.1.4 changes; owner still dissatisfied with overall UI and execution. Code/CI changes are not a substitute for owner acceptance.

## 18. Product decision log

D001 Keep one Javo Agents repo/app ID — FINAL.
D002 Android standalone mandatory; Windows optional — FINAL.
D003 Phone voice/chat is primary — FINAL.
D004 Official API, approvals and budget cap — FINAL.
D005 Five-product roadmap uses shared Javo Core — PRIOR STRATEGY.
D006 Social Publisher separate product may reuse Core — USER-DEFINED SEPARATE PROJECT.
D007 Wake word variant "Hey Jarvis" / "Hey Javo" — USER-CONFIGURABLE FUTURE FEATURE.
D008 Live Facebook Profile auto-publishing — NOT PROMISED, platform-limited.
D009 Public distribution, merge, billing and cloud hosting — NOT APPROVED.

## 19. Required engineering reporting format

For each feature provide: ID; user story; actual repo paths; build commit; requirements satisfied; P0/P1/P2 status; screen state; permission/security rules; tests executed; test results; environment; external blockers; next action; owner validation.

**Source references (internal):** JAVO_5_Projects_Master_Documentation.docx (12 Nov 2026); Javo Agents PR #1 and alpha-release-deliverables.md; Android field-testing messages through 13 Nov 2026; Javo Social Publisher SETUP_HINDI.md. Treat past assistant suggestions and historic product pitches as architecture proposals unless the owner explicitly selected them.
