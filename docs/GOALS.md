# Saved goals and manual evidence

Goals now read the authenticated local runtime instead of the sample Zustand
store. Create/edit/status/remove, manual measurements and milestone changes are
persisted in SQLite. This increment does not schedule agent work or experiments,
collect live account analytics, or promise a growth outcome.

An objective records metric/unit, baseline and its source, target, constraints,
stopping conditions and uncertainty. Measurements record a finite value, a
source and an offset-aware observation timestamp. They are owner-reported,
not independently verified platform results. The UI records the current time;
the API also accepts earlier observations if they are not older than the latest
saved observation. Measurement audit entries survive removing a goal.

Progress has one definition across list/detail/progress endpoints:

- Objective with a measurement: `(value - baseline) / (target - baseline)`.
- Objective without a measurement: zero, explicitly unmeasured.
- Legacy goal with milestones: mean of each milestone's current/target ratio.
- Otherwise: the legacy saved manual percentage, labelled as such.

Percentages are clamped to 0–100. Decreasing objectives work with the same
formula. Milestone completion is derived from its saved numeric values. A
goal's status changes only when the owner selects a status; reaching a value
does not manufacture an independently verified completion claim. Once a
measurement is saved, the objective is fixed to preserve its meaning. A new
baseline/target requires a new goal. Titles/descriptions/deadlines remain editable.

API paths under `/goals` and `/api/goals` share the existing single-owner token
boundary. Client-supplied ownership cannot select another user. The old
synthetic `default-user` ID is recognized as the local owner's legacy alias;
arbitrary database users are not. There is no multi-user login/pairing claim.
Objectives/evidence use the existing JSON column, so no destructive migration
is required. All mutation read/modify/write operations take a SQLite immediate
transaction to prevent lost measurements during simultaneous metadata edits.
Goal and milestone reads share an explicit SQLite snapshot so concurrent edits
cannot combine an old goal title with new milestone progress. New structured
evidence is versioned; opaque legacy metadata remains readable, and damaged
versioned evidence reports unavailable rather than silently becoming zero use.
Goal removal detaches associated tasks and retains their execution history;
milestones belonging to the goal are removed. Audit entries are retained.

Dates entered in the UI mean end-of-day Asia/Kolkata. API writes require an
explicit timezone and normalize to UTC. Legacy naive SQLite dates are read as
UTC; this cannot recover a timezone that an earlier version never recorded.

Verification:

```powershell
.\services\local-runtime\.venv\Scripts\python -m pytest tests/integration/test_goals.py -q
$env:JAVO_PLAYWRIGHT_MODULE='path/to/node_modules/playwright-core'
.\services\local-runtime\.venv\Scripts\python scripts/verify-dashboard.py --scenario goals
```

The browser harness uses temporary data and the real HTTP/database path. It
creates a goal, records evidence, completes a milestone, reloads and authenticates
again, edits/status-changes the goal, checks a mobile viewport, and removes its
test records. It performs no live platform, model or paid request. This is not
a hardware benchmark, full accessibility audit or complete ecosystem acceptance.
