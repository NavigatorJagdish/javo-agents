# Durable AI usage and zero-cost policy

Every router generation reserves an ID in a SQLite accounting file before
provider dispatch, then records completion or failure. The default location is
`usage-ledger.sqlite` beside the encrypted provider configuration. An explicit
`JAVO_USAGE_LEDGER_PATH` can choose another retained path. Counts are shared
across routers/processes and survive restart; earlier in-memory history cannot
be recovered. `coverage_since` records when this ledger began.

The ledger stores model/provider identifiers, timestamps, state, token counters
and integer micro-USD accounting amounts. It does not store prompts, response
text, keys, provider endpoints or private conversation history. It is a local
SQLite accounting file, not an encrypted full-user-data backup. Retain it with
the runtime profile; encrypted full-profile recovery remains separate work.

Only provider-reported integer token counts are treated as known. Missing or
invalid counts remain unknown and are counted explicitly. Local Ollama has no
provider API charge; electricity and hardware costs are not included. A broken
ledger blocks dispatch and reports unavailable rather than inventing zero use.
Cancellation and transport failure persist an unsuccessful attempt.

The old approximate model-price table has been removed. Cloud adapters and the
router reject cloud execution even if environment budgets are positive. Saving
a cloud credential or choosing it as the default does not authorize spending.
Paid budget edits remain disabled. This increment makes no real cloud request
and verifies no current cloud model price, free-tier entitlement or API quota.

The accounting core is prepared for future verified maximum quotes and actual
settlement. Atomic SQLite immediate transactions count existing reservations
and settled costs before admitting another reservation. Repeated IDs do not
authorize duplicate dispatch. Unknown cloud outcomes retain their maximum
hold across process restarts and UTC day/month boundaries, until independently
reconciled. Unexpected actual overruns are recorded truthfully and count against
later admissions. The core's trusted quote/settlement operations are not exposed
as user-supplied HTTP overrides and do not themselves enable a provider.

Budget periods use UTC request admission dates. Unresolved holds from earlier
periods also count against current limits. This is local accounting policy,
not a provider invoice reconciliation guarantee. Per-task/account spending
controls, verified price schedules, rate/quota acquisition, explicit paid
activation, reconciliation UI and encrypted full-profile backups remain pending.

Authenticated `GET /settings/ai-usage` (also `/api/settings/ai-usage`) reports
saved completed/failed/unresolved counts, reported tokens, missing-count totals,
charges/holds, coverage and timezone. Settings displays these values and an
unavailable state if storage cannot be read. Budget Guardian reads the same
ledger and refuses fabricated caller-provided spend receipts.

Tests use real SQLite, concurrent writers, an independent Python process and
synthetic HTTP transports. They verify persistence/idempotency, admission caps,
unknown outcomes, period rollover, cancellation, overruns and fail-closed
storage. The usage browser scenario seeds labelled synthetic usage, then reads
the actual API/database totals before/after reload; it is not model or billing
evidence. Run `python scripts/verify-dashboard.py --scenario usage` with the
documented Playwright driver and built dashboard.
