# Explicit timed simulation

Content schedules remain inert until reviewed, approved in `mock` mode and
explicitly armed. Approval alone does not start a timer. Live posting remains
unavailable. The default five-second worker checks at most 20 due timers per
iteration, serially, with a 30-second dispatch grace period.

1. Create a future schedule with an explicit timezone (UI uses IST).
2. GET `/api/content/schedule/{id}/preview` and review its exact snapshot.
3. POST `/api/content/schedule/{id}/approve` with `mode: mock` and its fingerprint.
4. POST `/api/content/schedule/{id}/timer` with that same fingerprint.
5. Keep the runtime running and resumed. GET `/api/content/timers` for status;
   GET the schedule's `/receipt` for a persisted simulated result.

DELETE the schedule's `/timer` to cancel armed/held work. Executing/completed
work cannot be declared cancelled. Manual `publish` remains an immediate
simulation, independently of planned time, using the same approval/dedupe policy.

Timer states: `armed`, `executing`, `simulated`, `held`, `cancelled`.
Before dispatch, a conditional database update durably claims armed work.
The armed fingerprint and current mock approval must still match the content.
The shared dispatcher checks pause/emergency-stop and persists publication
intent before the mock connector is called. Receipt uniqueness prevents a
second dispatch attempt from creating another simulated publication.

At startup, expired armed timers and interrupted executing timers are held.
Future timers remain armed. At due time, paused/stopped, late, changed,
unapproved or unconfirmed work is held, not automatically retried. Inspect the
receipt and create/review/approve a new future schedule when appropriate.
Resuming autopilot does not release held timers or create a catch-up burst.

Schema is additive: `publication_timers` is created by the existing table
initialization. Source backups and runtime-user-data backups are separate.

Validation: synchronous real-SQLite policy tests and fixture-based Chrome UI
approval/arm/cancel checks passed. The real async polling worker, production
async SQLite concurrency, actual wall-clock firing and full HTTP lifecycle are
not newly verified because this Windows environment's minimal asyncio probe
hangs before importing Javo. The added HTTP integration case must pass in a
working runtime before this feature is considered production-ready.
