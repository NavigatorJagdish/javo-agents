# Rebuild evidence and remaining scope

Checkpoint: 14 November 2026. This is an implementation increment, not a production release.

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
