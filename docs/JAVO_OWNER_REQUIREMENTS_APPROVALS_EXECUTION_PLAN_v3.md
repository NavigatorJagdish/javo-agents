# JAVO — OWNER REQUIREMENTS, ASSISTANT PROPOSALS, APPROVALS & EXECUTION BOARD
**Version:** v3.0 · **Date:** 13 November 2026
**Repository:** private NavigatorJagdish/javo-agents · **Branch:** fix/android-ci-and-production-hardening · **PR:** #1
**Authority:** owner turns in the current Javo Agents conversation, earlier recalled Javo/Jarvis conversations and explicitly selected proposals; source/strategy baseline docs/JAVO_COMPLETE_ECOSYSTEM_MASTER_SPEC_v2.md and the 25-page NOV 12 five-product planning document.

## Rules for interpreting owner intent
- **DIRECT / APPROVED**: the owner explicitly requested, said to include, or accepted suggestions. Treat as committed product scope, with delivery staged by feasibility.
- **PROPOSED**: assistant engineering/commercial recommendation without an explicit owner decision. Do not present it as owner-approved.
- **RESTRICTED/DEPENDENT**: legitimate provider approval, hardware/OS, infrastructure, economics, or credentials must be verified before claiming delivery.
- **IMPLEMENTED-IN-CODE** does **not** mean tested on owner phone or production complete. A green CI is not user acceptance.
- No source contains authorization to **merge PR #1, make repo public, publish to app stores, connect or post to an owner's social accounts automatically, spend money, or buy hosting**. These always remain owner-gated.
- Past assistant replies sometimes said an initial product strategy was approved; the explicit user records demonstrate approval of the 6 features and 10 modules, not a firm approval for all launch order/pricing guesses.

## A. Explicit owner requirements (binding)
| ID | User instruction / original intent | Confirmation/approval evidence | Priority | Actual known status / dependency |
|---|---|---|---|---|
| O-01 | Company/product brand **Javo Agents**, professional logo and consistent app/website UI | User named product and requested logo/UI | P0 | Brand/app exists; owner dislikes current UX |
| O-02 | **Same existing ecosystem/app**, not a second replacement Android app | “isi app me apne ecosystem me add krna hai” | P0 | One private repo/package retained |
| O-03 | Android app runs **without a PC** for everyday use | User said PC-less users must use it | P0 | Standalone routing/code exists; owner hardware testing incomplete |
| O-04 | Windows enhanced mode optional; Windows offline must not block Android | Explicit PC dependency complaint | P0 | Mode present, integration limited |
| O-05 | Natural two-way **Hindi/Hinglish/English speech**, assistant listens **and speaks actual reply** | Repeated direct asks and device bug reports | P0 | STT/TTS code, owner errors 11/13 and stuck Listening |
| O-06 | Mobile **API key entry**, real Gemini BYOK and selectable provider | User explicitly complained option missing | P0 | UI/Keystore code, actual key/live reply not verified |
| O-07 | Phone **social-account Add/Connect** for Facebook, Instagram, YouTube | Repeated owner complaint | P0/P1 | Cards only; full provider OAuth not delivered |
| O-08 | **Master Agent, autonomous workers, proactive monitoring** | User explicitly selected trio | P0/P1 | Catalog and prompt orchestration; actual bounded tool runs incomplete |
| O-09 | True phone-executable tasks and agent results, not just a list of roles | User dissatisfied that app only lists tasks | P0 | Partial real model-based task responses; tool actions limited |
| O-10 | Real notifications, reminders, including 8 AM and optional reconnect/check-in after ~1–1.5h | Explicit user voice requests | P1 | WorkManager baseline; recurrence/OS/hardware acceptance pending |
| O-11 | Opt-in context learning, long-term memory and user controls | User wants assistant to learn conversations | P1 | Opt-in encrypted chat and bounded multi-turn text implemented in code; full semantic memory not built |
| O-12 | “Hey Jarvis” wake phrase, hands-free, background/lock-screen use where possible | Repeated owner device requests | P2 | Hands-free foreground code; OS/battery/policy-bound wake word unimplemented |
| O-13 | User-controlled Android app opening, gallery, YouTube, Instagram, contacts/call shortcuts | Explicit phone-assistant demands | P1/P2 | Actual action tools/permissions incomplete |
| O-14 | **Free-first; no forced paid APIs**, optional key entry; 8GB Windows resource awareness | Explicit owner conditions | P0 | Cost/usage guard design; real quota enforcement unverified |
| O-15 | Multi-agent roles: **AI Growth Scientist, Content Factory, Smart Memory, self-upgrading engineer, Telegram mobile command, multi-account Brand Manager** | Owner explicitly accepted all six suggestions | P1 | Catalog includes names; specialist tool validation varies |
| O-16 | Ten unique modules selected (see section C) | Owner explicitly selected 10/10 | P1/P2 | Mixed partial/unimplemented |
| O-17 | Premium futuristic navy/cyan/violet UI and consistent logo, useful mobile layout | User requested full app/website UI and repeatedly rejected current UI | P0 | Home redesigned code only; design/acceptance still open |
| O-18 | Full ecosystem website, Windows, Android, cloud-optional integrations | Explicit user direction | P1 | Website/runtime exist; parity incomplete |
| O-19 | Encrypted personal user data, safe permissions, independent app packaging | Explicit security and privacy constraints | P0 | Android encryption baseline; end-to-end security tests pending |
| O-20 | **Private GitHub initially**, later launch under owner control | Explicit initial private-first constraint | P0 | PR #1 private/unmerged |
| O-21 | A **complete master documentary** covering every small and large feature | Direct request; earlier five-product doc | P0 | v1 25-page plus v2 master spec and this decision ledger |
| O-22 | Build **Javo** as a revenue-generating AI software company over time | User explicitly requested business/product roadmap | P2 | Business roadmap exists; no paid launch approved |
| O-23 | Optional VPS/hosting for agent teams, monthly ₹500–₹1,000 without large advance | User specified monthly billing | P2 | Architecture recommendation, no host purchased or deployed by this task |
| O-24 | Quality, actual results, no fake tasks/approvals/analytics, owner acceptance | User supplied screenshots/complaints | P0 | Known fake data mostly removed; no final owner acceptance |
| O-25 | Concrete releases/versioned APK updates, instructions and trustworthy checksums | Repeated APK install/bug/release requests | P0 | Historical draft releases; current new changes lack verified artifact |
| O-26 | Javo Social Connector / Publisher as **separate** product when explicitly requested | Owner asked separate app, including Android-only | P2 | Maintain separation/reuse Core; not a second Agents app |
| O-27 | Private, consistent Javo ReVanced ecosystem, separate from Jarvis/Agents | Distinct project | OUTSIDE Agents | Do not bundle into Agents |
| O-28 | Separate visual comic images, batch of 10 until 100; eventual authorized social scheduling | Owner explicit Facebook content goal | INTEGRATION P2 | Social Publisher workflows separately; no unapproved automated profile posts |
| O-29 | More natural voices and realistic media/video outputs, distinct character dialogue, no still-only replacements | Owner creative product expectations | Studio P2 | Advanced media engineering not delivered |
| O-30 | After reviewing chat, build requested features and report completed/pending ordered | Latest explicit owner instruction | P0 | This board is the reporting source |

## B. Assistant suggestions and how to treat approvals
| Suggestion ID | Suggested idea | Owner response | Approval status | Decision |
|---|---|---|---|---|
| S-01 | 6 specialist features (Growth Scientist, Content Factory, Smart Memory, self-upgrade, Telegram command, Multi-brand) | Owner accepted all six | **APPROVED** | Include in capability roadmap, not claim runnable |
| S-02 | 10 differentiator modules | Owner accepted 10/10 | **APPROVED** | Maintain all ten in backlog and test matrix |
| S-03 | Five-product line: Social AI, Agents, Business, Voice/Jarvis, Studio | User requested a master doc covering five | **APPROVED AS DOCUMENTATION / STRATEGY**, not five live apps | Shared Javo Core, staged products |
| S-04 | Social AI first paid product; proposed 2026–28 release calendar | No explicit approval of exact sequence | **PROPOSED; NOT FINAL** | Android Standalone work takes current priority |
| S-05 | Free ₹0, Creator ₹299, Pro ₹799, Agency ₹2,499 | No explicit price approval | **PROPOSED** | No payments/subscriptions until owner authorizes |
| S-06 | Android-only, Windows enhanced, optional cloud operating modes | User explicitly reinforced same ecosystem PC-free | **APPROVED DIRECTION** | Android-core must not be gated by Windows |
| S-07 | Gemini BYOK/custom provider, optional Windows Ollama | User requested Gemini/free APIs and optional API | **APPROVED DIRECTION** | No silent model/provider switching |
| S-08 | Official OAuth for Facebook Pages, IG Professional and YouTube; manual Facebook Profile share | Owner requests account operations; no provider approval granted | **APPROVED GOAL, TECHNICALLY DEPENDENT** | Do not simulate OAuth/publish |
| S-09 | Always-on wake word/Accessibility-based phone-wide automation | Owner wants functionality; implementations constrained by OS/policy | **GOAL APPROVED, FEASIBILITY NOT ASSURED** | Test permission-compliant approach first |
| S-10 | Master Agent supervised task planning, approvals, logging | User selected master/workers/proactivity | **APPROVED** | Tool execution and proof required |
| S-11 | Adopt dark navy + cyan/violet, orb and conversational home | Requested theme / rejected card-heavy UI | **APPROVED DIRECTION** | Device screenshot/UX review still required |
| S-12 | Publish PR, merge, change repository visibility or buy VPS | Not authorized | **NOT APPROVED** | Do none automatically |
| S-13 | Full native Business/Studio suite shipped immediately in Android alpha | Not explicitly requested as release gate | **PROPOSED PRODUCT EXPANSION** | Future work; preserve five-domain strategy |
| S-14 | Cloud OAuth broker and reliable hosted scheduler | Needed for certain integrations but no hosting consent | **DESIGN RECOMMENDATION, BLOCKED ON DEPLOYMENT** | Specify and prototype safely, never claim live |

## C. Ten owner-selected differentiator modules
| ID | Approved module | Required acceptance test | Status |
|---|---|---|---|
| D01 | Quality Inspector | Actual draft audit output with evidence | PARTIAL |
| D02 | Account Guardian | Verified token/scope/expiry and actionable alerts | BLOCKED by OAuth |
| D03 | Competitor/Niche Radar | Permitted sources + timestamp + no fake metrics | PLANNED |
| D04 | Smart Approval Inbox | Real proposal → preview → one-time decision → trace | PARTIAL |
| D05 | Zero-Cost Budget Guardian | Hard quota / cap blocks spend | PARTIAL; not metered end-to-end |
| D06 | Content Recycling | Originality/duplicate guard on saved drafts | PLANNED |
| D07 | Brand Identity Studio | Persist brand kit and enforce tone templates | PARTIAL |
| D08 | Weekly Strategy Board | Verified metrics + reviewable recommendations | PLANNED |
| D09 | Offline Recovery/Backup | Restore backup with migration test and no loss | PARTIAL |
| D10 | Plugin Sandbox/Trust Score | Signed manifest, permission sandbox, negative tests | PARTIAL |

## D. Priority-ordered execution board
**Do not say 'complete ecosystem' while any P0 owner journey fails.** Work in dependency order and log evidence on every commit.

| Order | Work package | Requirement IDs | Done means | State as of this document |
|---|---|---|---|---|
| 01 | **CI + source integrity**: investigate immediate 5-workflow failure, lint/test/assemble and release immutability | O-19, O-20, O-25 | All tests on exact head green, sha/version record, no overwrite | **BLOCKED — GitHub Actions jobs fail before step logs** |
| 02 | **Phone AI setup**: visible account/API model setup, verified Gemini/custom test and explicit routing | O-03, O-06, O-14 | No Windows; real provider reply and key safe | **CODE; USER VALIDATION PENDING** |
| 03 | **Conversation engine**: STT Hindi/Hinglish, error 11/13 recovery, no stuck listening, TTS audible, cancellation | O-05, O-11 | 10 real phone turns, no false audio or actions | **CODE; USER VALIDATION PENDING** |
| 04 | **Context and memory**: bounded AI turns, provider separation, opt-in encrypted history, export/delete | O-11, O-19 | Correct follow-ups across restart when consented | **CODE PATCH; CI/DEVICE PENDING** |
| 05 | **Voice-to-Content Studio**: user approved save of actual generated AI reply as local draft | O-09, O-24, O-28 | Real saved draft, persists after restart, manual save only | **CODE PATCH; CI/DEVICE PENDING** |
| 06 | **Mobile task orchestrator**: real tool actions, persistent runs, progress and approvals | O-08, O-09, O-10 | Task output and trace show actual work | **PARTIAL** |
| 07 | **Android shortcuts/reminders**: opt-in phone Intents, scheduled notifications, safe prompts | O-10, O-13 | Execute on owner device, no OS bypass | **PARTIAL** |
| 08 | **Android UX redesign**: conversational Home, Work, Studio, Accounts, More, responsive accessibility | O-01, O-17 | Owner approves actual tested screens | **PARTIAL** |
| 09 | **Social OAuth**: legitimate account identities, token lifecycle and scopes | O-07, O-18, O-19 | Real Page/IG Professional/YouTube account connected | **BLOCKED on developer credentials/hosted broker/app review** |
| 10 | **Social scheduling/publishing**: creator drafts→approval→scheduled→provider receipt; manual personal Profile sharing | O-07, O-28 | Verified external receipt, no fake posting | **BLOCKED by 09 and live platform access** |
| 11 | **Agent differentiators**: all 10 special modules, six selected workers, budget guard | O-15, O-16 | Every runnable tool has positive/negative tests | **PARTIAL/PLANNED** |
| 12 | **Cross-device sync**: real Windows pairing, optional cloud, conflicts/ack/recovery | O-03, O-04, O-18 | Authenticated bidirectional sync and optional mode | **PARTIAL** |
| 13 | **Proactivity & wake word feasibility** | O-10, O-12 | Background behavior OS-compliant and opt-in | **PLANNED/OS-DEPENDENT** |
| 14 | **Full Studio/Business + five-product company roadmap** | O-22, O-23, O-29 | Separate vertical E2E acceptance, pricing trial only with approval | **PLANNED** |
| 15 | **Release and owner acceptance** | O-01..O-30 | Signed/versioned Android/Windows artifacts, real device tests, explicit approval | **NOT COMPLETE** |

## E. External prerequisites (not permission to simulate completion)
- Owner supplies platform developer app identity and configures eligible Facebook Page / Instagram Professional account / YouTube OAuth consent. Confidential provider client secrets belong only on secure backend, not in APK.
- Hosted broker/scheduler requires owner approval for hosting and billing; without backend, manual export/share must remain available.
- User must enter their own AI provider key, then validate an actual live response. Do not commit any secret.
- Physical Android 16 testing must be performed on real compatible device; CI/emulator tests alone are not proof.
- GitHub Actions runner/plan issue must be diagnosed from account Actions/billing/security logs; current connector logs are absent/BlobNotFound.
- Public release, PR merge, mobile publishing, app-store distribution and paid subscriptions require separate explicit owner authorization.

## F. Recent implementation evidence / not yet a release
Existing branch now contains:
- Voice-first Home; AI provider selection persisted and honored by chat/agent execution.
- Configured-vs-running agent labels, removal of unknown-agent fallback, bounded Error 11 retry.
- Opt-in encrypted local chat and 12-turn bounded provider-isolated context.
- Gemini credentials in header; provider-failure messages not spoken as successful AI replies.
- TTS engine readiness/cancel hardening.
- A new real **Save as Content Draft** action for verified Gemini/Custom AI replies, requiring user click and platform selection.
- Regression tests added in KeystoreManagerTest and GeminiApiClientTest.
- CI release upload guarded by explicit manual opt-in; older same-version release asset has checksum drift from previous workflow.
**All these are CODE-LEVEL changes.** No fresh APK or real device acceptance has been verified for them.

## H. Current implementation progress and issues (13 November 2026)

- **Private owner requirements and approval ledger:** `docs/JAVO_OWNER_REQUIREMENTS_APPROVALS_EXECUTION_PLAN_v3.md`
- **CI release blocker:** [Issue #2](https://github.com/NavigatorJagdish/javo-agents/issues/2). Latest PR runs still fail before usable job steps, even on Windows/Backend/Frontend/Security; source compilation for newer changes is **NOT VERIFIED**.
- **Physical Android acceptance:** [Issue #3](https://github.com/NavigatorJagdish/javo-agents/issues/3). Requires owner device, actual STT/TTS and 10 turns.
- **Mobile social OAuth:** [Issue #4](https://github.com/NavigatorJagdish/javo-agents/issues/4). Requires real OAuth app credentials and optional hosted broker.
- **Latest code changes:** Genuine user-confirmed **Save as Content Draft** per verified AI reply; `isVerifiedAiReply` proof field and legacy migration-safe default; default Gemini 3.5 Flash-Lite and selectable Gemini 3.8 Flash; removed discontinued Gemini 2.0 model and false fixed free-RPM claims; selected-provider-specific readiness on Home; redacted custom errors and blocked keys over cleartext HTTP; social handle placeholder creation disabled; static "Active agent" statuses corrected; unimplemented $0 guard clearly disclosed rather than falsely presented as enforced.
- **Current release:** NO new versioned APK is built or published for these source changes. Do not suggest that old `v0.1.4-alpha` packages contain them.
- **Follow-up note:** The exact feature acceptance definition includes device tests, negative tests and private release SHA/version provenance; a file committed to GitHub is not a completed feature.

## G. Reporting format for every subsequent iteration
Requirement ID → implementation path and commit → executable test and CI status → actual device/account evidence → result (DONE / CODE ONLY / BLOCKED / PENDING) → next dependency. Never conflate “requested,” “approved,” “implemented,” and “shipped.”

**Repo decision:** preserve this as the execution contract. If the user changes scope, add a versioned amendment; do not silently erase old decisions.
