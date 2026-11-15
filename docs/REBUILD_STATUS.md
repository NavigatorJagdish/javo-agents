# Rebuild evidence and remaining scope

Current review: 15 November 2026. This is an unfinished rebuild, not a production release.

## Saved Goals increment — local Windows evidence

The Goals screen now uses real owner-scoped persistence, manual measurement
sources/history, milestones and consistent progress. Goal deletion preserves
task execution history. See GOALS.md for ownership, migration and evidence
boundaries. It does not generate automatic experiments or claim live analytics.

Current local backend checks: 154 passed, one platform skip and one upstream
TestClient deprecation warning (125.13s). Added 11 real HTTP/SQLite goal cases
and an explicit resource-pressure rejection regression. Synthetic companion
tests now use deterministic capacity measurements; actual production resource
safeguards are unchanged. Dashboard and shared-client TypeScript builds passed.
Chrome completed GOALS_REAL_DATABASE_CREATE_MEASURE_MILESTONE_RELOAD_EDIT_REMOVE_OK
with temporary real backend/data and a 390px overflow check. Visually inspected
the mobile screenshot. This is not full accessibility or design-reference QA.

Fixed test harness cleanup on Windows to terminate its owned process tree;
a venv launcher otherwise leaves the interpreter/database open. The rerun
completed successfully with temporary-directory cleanup. Added Goals coverage
to Windows CI, but that new CI check has not yet run on this revision.

At commit `25ab3154eb683a8e3d05649d91fe7d2ea4dd9a89`, all four GitHub
workflows passed: backend 43717423145, frontend 43717423144, security
43717423275 and Windows 43717423140. Windows job 132821858348 also passed
the new frozen-backend Goals browser scenario, packaged controls/restart,
unsigned package builds and NSIS uninstall/reinstall. The new CI pass supersedes
the preceding pending-CI statement for that exact commit only.

## Durable API accounting increment — local Windows evidence

Replaced process-only router counters and approximate hard-coded prices with
persisted usage, atomic reservation/settlement and explicit unknown token usage.
Settings and Budget Guardian read the same ledger. Cloud adapters cannot be
enabled by positive environment budgets; verified prices and explicit spending
authorization remain required. See AI_USAGE.md for remaining quota, paid
activation, recovery and account/task budget work.

Local full backend run:165 passed, one platform skip, one dependency warning
(134.37s), followed by23 targeted accounting/routing/safety passes including the
final duplicate-dispatch regression. All backend/test Ruff and Bandit -ll
checks passed. Dashboard build passed. Chrome usage scenario completed
USAGE_SAVED_API_COUNTERS_RELOAD_OK against actual saved synthetic records.
This is persistence/UI evidence, not a real cloud billing or model-quality test.

Current source and CI: [draft PR #5](https://github.com/NavigatorJagdish/javo-agents/pull/5).
Linux full-suite, Windows standalone/browser/packaged-app and NSIS QA-profile
install/uninstall/reinstall checks have passed. Provider configuration now
uses authenticated encrypted persistence, OS/user-backed Windows keys, shared
router configuration, safe metadata and explicit credential removal. The UI
performs actual saves; cloud budget increases remain blocked pending durable
spending controls. See PROVIDER_CONFIGURATION.md and WINDOWS_PACKAGING.md.

The initial matrix and early blockers below are historical; later dated
evidence supersedes them. No live posting, signing or final release is claimed.

## Text companion and fresh-install regression — 15 November 2026

The Voice screen and API now perform real audited runtime controls and bounded
text inference through the configured AI router, without tools. Resume requires
confirmation; local AI is default, cloud selection clears prior context, and
zero-cost budgets apply. Cancel/disconnect and emergency-stop cancellation use
the actual worker pool. Fake sample messages, Whisper readiness, silent WAV and
transcription success were removed; audio endpoints return 501.

Focused API/cancellation tests: 18 passed. Full backend suite: 142 passed, one
platform skip. Skill tests: 14 passed. Desktop tests: 17 passed with the updated
builder dependency and frozen lockfile installation. Ruff and Bandit passed.
Dashboard TypeScript/Vite build passed.
Browser flow uses a temporary loopback model fixture, not a real model; fresh
Windows packaged verification is required for this increment.

Current-head cffa5a5 Windows CI twice passed frozen browser and packaged DPAPI
save/restart but failed NSIS installation with 0xC0000005 (first attempt during
reinstall; retry during fresh install). Earlier successful installers do not
certify this head. Electron-builder is pinned to 26.9.0, containing upstream
Windows-version gating for the known per-user installer crash (PR #9564). Full
install/uninstall/reinstall must pass again. The QA extension preserves encrypted
provider data and the DPAPI-wrapped key across uninstall/reinstall, then verifies
real UI decryption. Uninstall uses the documented synchronous `_?=` option.

See COMPANION.md for capabilities and remaining audio work.

## Initial baseline — historical

Source: NavigatorJagdish/javo-agents at 133be3a085a6460b28e1b76f50cde9c68062766d.
368 source files were retrieved through the connected repository service and matched against Git blob hashes after shell clone failed DNS. Local baseline af32fce has snapshot history, not upstream ancestry. Branch rebuild/runtime-foundation is local only; do not force-push it. Remote was public, whereas the owner requested private development.

| Requirement | Implemented increment | Remaining verification/work |
| --- | --- | --- |
| 8GB minimum, scale upward | Hardware-based profiles, RAM headroom, fixed worker pool, bounded queue | Real 8GB/larger hardware benchmarks; VRAM-aware scheduling; async cancellation tests |
| Local authorization | Owner bearer boundary on API aliases and WebSocket; Electron main-process credential; browser memory-only credential gate | End-to-end Electron/HTTP/WebSocket checks, pairing, scoped device tokens |
| Honest publishing | Persisted approval fingerprints, durable unique dispatch attempts, explicit mock receipts, no fabricated published status | Live OAuth/capability/receipt verification; async race and restart tests; scheduler-to-publication wiring |
| Approval and failure handling | Missing high-risk manager holds work; caller approved flag cannot bypass review; failed dependencies block downstream work | Durable general approval inbox and resumable orchestration |
| Restart scheduling | Start paused, hold overdue jobs, one instance per job, explicit timezone | Real restart integration checks, durable review UI |
| Dashboard | Auth gate, matching API prefix, real home status/schedules, no silent mutation success fallback, confirmed control responses | Dependencies/build unavailable; other pages remain prototypes and are labelled; API DTO alignment |
| Windows startup | One runtime owner; hidden headless process; token required | Installer, shutdown, packaged startup and port checks |
| Free now / paid later | Requirements retained; no paid activation or spending | Provider configuration persistence, explicit budgets, quota enforcement |
| Remaining ecosystem | Original complete specification retained in project memory | Android, website, official connectors, voice, Telegram pairing, encrypted vault/backups, sandboxed upgrades, analytics, design-reference fidelity, release pipeline |

## Evidence

- Initial existing suite: 23 tests collected, not passed.
- Publication/resource/auth regression suite: initial 16 tests passed, then extra orchestration/scheduler/route checks added. See current test output for final count.
- SQLite rule tests use real synchronous transactions behind an awaitable adapter. They do not prove the production async driver, HTTP lifecycle, concurrent execution, remote publication or full restart recovery.
- Full suite retried after reconnect and timed out after 40 seconds before first result. Previous stack trace stopped in Windows asyncio socketpair startup. No integration pass claim.
- Frontend offline dependency installation failed ENOTCACHED for @headlessui/react. Frontend build, visual inspection and Electron typecheck are not verified.
- Python compileall previously passed; repeat after final edits.

## Next actions

1. Finish async worker/restart/HTTP tests in a working execution environment; verify pause/emergency cancellation under load.
2. Install dependencies through an available authorized network route, typecheck/build dashboard and Electron, then inspect actual UI.
3. Complete one import/draft/approve/schedule/mock-receipt flow in UI before enabling live connectors.
4. Replace prototype stores/screens incrementally and implement durable credentials and budgets.
5. Inspect original design references; implement remaining surfaces against the full memory requirements.

Final verified checkpoint: 20 targeted synchronous regression tests passed in 4.13 seconds; Python compileall, git diff --check and PowerShell startup parser checks passed. Three async worker lifecycle regression tests were added but are not claimed executed successfully.

Frontend online dependency retry also failed: DNS ENOTFOUND registry.npmjs.org. Build remains blocked by unavailable dependencies.

## Content workflow increment

Content page now calls real import, schedule, preview, approval and mock-dispatch handlers. It also reloads persisted receipts. Approval requires the SHA256 fingerprint returned by the exact preview reviewed, preventing changes between preview and approval from being accepted silently. Manual simulation is explicitly immediate; automatic timed dispatch and live posting remain unavailable.

Validation: 24 targeted synchronous regressions passed (10.65s); compileall and diff whitespace check passed. No frontend build, HTTP lifecycle or UI end-to-end pass is claimed. Current blockers remain npm dependency network access and Windows asyncio startup. API clients must send mode and fingerprint to approve; obtain fingerprint from the preview endpoint.

## Durable control step

Added atomic non-secret control-state storage and restart restoration. Missing state starts paused. Invalid state holds automation. Resume persists before workers are released; API and Telegram share controls. Startup respects held state; manual resume reconciles overdue jobs. Dashboard derives control status from the backend.

36 targeted tests passed in 4.93s, including 12 real-file persistence and failure tests. Three async worker tests collect but have not passed execution. Python compileall and diff checks passed. Full process restart and frontend verification remain outstanding. A failed stop-state write still stops current in-memory work but cannot guarantee persistence across restart; the command reports failure.

## Verified startup/integration checkpoint

14 November 2026: previous asyncio environment blocker did not reproduce. Minimal diagnostic returned ASYNCIO_OK. Full existing backend suite: 73 passed, 1 warning in 49.61s. This includes three async worker tests, real HTTP/async-SQLite content approval and simulated-receipt flow, pending-task emergency cancellation and two independent runtime processes verifying persisted emergency-stop and paused scheduler state.

Fixed nonexistent task-state enum usage and startup resource leaks using AsyncExitStack. Added seven fault-injection cleanup cases. Updated authorized Telegram/voice test fixtures. compileall and diff checks passed.

Older integration-blocked entries above are historical. Frontend build/visual/Electron checks and original remaining product requirements are still incomplete. Process test uses FastAPI TestClient lifespans and is not an installer or live port verification. Passing mock/prototype tests is not proof of complete production features.

## Frontend verification checkpoint

Dashboard typecheck and production build passed; Windows shell typecheck and TypeScript build passed. Headless Chrome against an isolated real runtime passed owner login, resume, import, schedule, review, approval, simulation and receipt reload. 390px mobile overflow and page-error checks passed. Fixed old local-only Autopilot click handler, explicit select labels and health-driven availability badge.

Successful install used npm ranges with package-lock disabled and install scripts ignored after pnpm stack/symlink failures. pnpm lockfiles unchanged; exact locked release install remains outstanding. JS initial bundle 997.36 kB (gzip 288.86 kB); route splitting needed. Electron binary/installer and visual reference fidelity remain unverified. See scripts/verify-dashboard.py and scripts/dashboard-smoke.cjs for repeatable browser coverage.


## Route splitting, desktop lifecycle and backup increment

14 November 2026 (owner C-015/C-016): all 27 dashboard routes now load lazily.
Main JS entry decreased from 997.36 kB (gzip 288.86 kB) to 288.82 kB
(gzip 91.30 kB), about 71% less raw entry JS. Heavy analytics/workflow chunks
load on demand. Layout controls remain mounted while routes load; a failed
chunk has an error boundary and navigation recovery. This measures bytes,
not hardware performance or initial network latency.

Dashboard typecheck/build passed with no large-chunk warning. Browser-only
route verification passed using explicit API fixtures: deferred heavy routes,
Content loading fallback, retained emergency control, workflows/analytics/setup
chunks, deliberate chunk failure and recovery by navigation. This is not a
repeat pass of the real backend content flow. The real-backend smoke retry
was blocked at readiness; the independent minimal Python asyncio diagnostic
again hung in Windows socketpair setup. Earlier 73-test/backend and real
browser results remain historical evidence.

Desktop changes: writable per-user runtime data, Python source import path,
readiness-based running state, handled missing-Python spawn errors, single
concurrent startup, stdout draining, backend-derived tray controls, and awaited
bounded shutdown. Desktop typecheck/build passed; missing-Python test passed.
Full HTTP child-process lifecycle test has not passed in this execution window.
Electron binary download failed DNS resolution for github.com; no Electron
window, packaged installer, or end-user Python distribution is verified.
Existing developer databases are preserved at their prior locations; migration
into the new per-user data folder is not implemented. Credentials/data encryption
and runtime dependency bundling remain required release work.

Owner authorized Google Drive backups, GitHub source checkpoints and cleanup
of unnecessary storage. See BACKUP_POLICY.md. New create-checkpoint.py creates
credential-filtered source archives with manifests and extraction/hash checks.
Remote upload receipts and cleanup evidence belong to private project memory.
No installer is labelled final or ready to install in this increment.

## Bundled runtime and desktop readiness increment

Added a Windows x64 PyInstaller build script and dedicated backend entry point.
Packaged Electron launches the bundled executable directly, while developer mode
retains Python. Missing packaged runtime does not fall back to system Python.
Packaging preflight and electron-builder beforePack verify dashboard/icon/runtime
presence, Python DLL, import-test evidence and payload SHA256 hashes. Build-time
publishing is disabled. See WINDOWS_PACKAGING.md for procedure and acceptance.

Fixed desktop readiness accepting a degraded database response as ready, stop
during asynchronous port allocation spawning a late backend, and a late health
response marking a stopped backend ready. Corrected the older Node test mock
cleanup API from mockFunction.restore() to mockFunction.mock.restore().

New isolated contract checks: 11 passed (0.67s), using mocked process/network
boundaries and temporary package fixtures. These do not prove live process/HTTP
behavior. Unfrozen Python entry point import check returned RUNTIME_IMPORTS_OK
with 30 registered agents; this is not evidence of a frozen executable working.
Desktop TypeScript build and changed-Python syntax checks passed.

Current packaging blockers: configured Python index provides no PyInstaller;
minimal asyncio probe again timed out in Windows socketpair before app import.
Electron binary and complete installer execution remain unverified. Existing
historical backend/browser passes remain historical, not fresh verification.

## Package provenance follow-up

Backend bundles now record Python source and dependency-declaration hashes.
Preflight rejects changed/added/deleted source, missing source provenance and
extra payload files absent from the manifest. Build rejects source changing
during bundling. Fifteen isolated desktop contract tests passed; this still
does not verify a frozen executable or an installed desktop app. Cache cleanup
was repeatedly interrupted and is deferred; no reclaimed-space claim.

## Timed simulation and backup hardening — 15 November 2026

Explicitly approved mock schedules can now be armed for timed simulation and
cancelled from the Content page. Durable timer claims, exact snapshot checks,
pause/stop holds, 30-second late holds and startup recovery avoid automatic
catch-up. Timers and receipts are distinct persisted records. Live publishing
is still unavailable. See CONTENT_TIMERS.md for API and execution limits.

Settings backup now uses a real SQLite online snapshot and encryption with a
configured persistent key; missing key/database cannot produce empty success.
Unsafe live database overwrite is disabled. Archive restore stages into an
empty directory with member/path checks, and recovery agent no longer reports
fake restoration. See BACKUP_RECOVERY.md; complete OS key storage, full-data
backup and automatic offline installation remain unfinished.

Latest local evidence: 77 targeted synchronous tests passed (5.71 seconds),
14 existing skill tests passed, dashboard TypeScript/Vite build passed and
Chrome fixture-based route plus approval/arm/cancel checks passed. Full Ruff
check across backend, skills and tests passed after cleaning earlier lint
errors. Bandit -ll static scan returned no findings; this is not a complete
security audit. Compile and diff checks passed.

The independent asyncio probe still hangs in Windows socketpair before Javo
imports. New HTTP timer test is present but not passed locally; full async
polling/HTTP/installer verification remains outstanding. Historical full-suite
results are not a new verification of these changes.
