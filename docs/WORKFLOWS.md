# Saved workflows and manual local drafting — 17 November 2026

Workflows now saves/reopens real graphs, keeps definition revisions and runs a
bounded subset through an actual durable worker. It does not activate automatic
triggers, social publishing, approvals, notifications or every catalog node.

## Saved definitions

Each save preserves node IDs, positions, labels, configuration, connections,
description and status. It creates a new revision and graph fingerprint.
Updates/restores/removal require the current expected revision: stale writes
return409 and leave both the saved version and the editor's pending edits
intact. Save as new copy remaps node/edge identifiers and retains the original.
Restore creates a new revision rather than rewriting history.

The API rejects duplicate IDs, another graph's IDs, dangling connections,
duplicate edges, cycles, invalid positions, nonfinite nested values, excessive
nesting/size and unknown input fields. Definitions are limited to64nodes,
128connections and128KiB serialized data. Empty/disconnected planning drafts may
be saved; the executor applies additional requirements before queueing.

Only token-authenticated `local-owner` and the prior synthetic `default-user`
alias are accessible. New rows use the canonical local owner; callers cannot
select another owner. Read snapshots keep graphs and revision numbers consistent;
immediate SQLite mutation transactions serialize changes. A new additive
workflow_revisions table preserves original workflow data. Legacy active/invalid
definitions remain readable with limitations and need repair/review before use.

This is ordinary SQLite workflow data, including saved prompts, trigger inputs,
revision snapshots and generated outputs. Do not put credentials in it. The
definition fingerprint detects changes, not hostile filesystem access by an
attacker able to rewrite the database and its hashes.

## Supported manual execution

An executable draft has exactly one manual Trigger, a single connected path,
and a final End. Supported intermediate nodes are local AI Prompt and Delay.
Branches/joins/conditional edges and other node types fail before enqueueing.
Advanced nodes are visibly labelled save-only in the editor.

- Trigger and End: empty configuration object.
- AI Prompt: `prompt` (1–8000characters), `provider: "ollama"`, optional
  `max_tokens` (integer1–1024, further bounded by saved provider settings).
- Delay: `seconds` (finite number0–30). Total configured wait is at most30s;
  at most three AI prompts per run.

Review sends the saved revision/fingerprint and a bounded JSON trigger object.
The server creates a queued receipt with a fixed graph/authorization snapshot,
then an actual worker claims it after normal capacity/control checks. Editing a
definition does not rewrite an already reviewed run. Each AI node receives the
owner's instruction, trigger data and previous text output in a JSON envelope.
It has no action tools; text cannot approve, publish or verify account results.
Only the configured local adapter is used, with no cloud fallback. As with any
user-controlled loopback service, verify its own execution/privacy/cost policy.

Node start/completion and actual output are saved. A model failure produces a
failed run, never a successful fallback message. Successful-run counts exclude
old prototype receipts. Historic raw counters remain separately reported.

The saved queue is bounded, and only one active run per workflow is accepted.
Runs expire five minutes after enqueueing when checked for dispatch; an admitted
run has a180s lifetime. Resource limits are unchanged. Pause holds between nodes;
it does not undo work already in flight. Owner cancellation/emergency stop
interrupts supported running operations and prevents late success overwrites.
Archiving prevents/interrupts execution; definition pause holds queued work.
Use explicit cancellation when a reviewed snapshot should never run later.

An OS lease prevents competing workflow dispatchers for one database. Queued
reviewed runs survive restart; interrupted runs become failed/unconfirmed and
are not automatically replayed. Graceful shutdown cancels owned active work.
The worker shares the bounded production resource manager with other local
operations. Execution history blocks destructive workflow deletion; archive
the definition instead. Unused definitions can be explicitly removed.

## Editor and practical safeguards

The real graph editor maps ReactFlow to the runtime schema, supports keyboard
connection controls, refuses circular connections, preserves JSON configuration,
and fits the graph after viewport resize. Save/reload errors remain visible.
Unsaved edits block in-app route changes and warn before page reload/close.
Graph selection/new/template/reload ask before discarding pending edits. Browser
force-close/crash recovery of unsaved tab memory is not implemented.

Revision history and recent execution receipts are read from the runtime. The
current UI shows up to50recent entries; API revision listing supports pagination.
An explicit supported manual run replaces the old visual animation/fake running
receipt. Planning nodes remain available without pretending to execute them.

## Evidence and limitations

Integration tests use actual HTTP/SQLite/worker/control/restart behavior and
labelled synthetic model text. They cover save/restore/conflict, owner and ID
isolation, invalid graphs, bounded configuration, queue/run cancellation,
emergency interruption, pause, archived/expired/tampered/legacy runs and history
retention. The browser scenario uses a synthetic loopback model behind the real
router/usage ledger; it is not model-quality or live-publishing evidence.

`scripts/verify-dashboard.py --scenario workflows` checks real save/reopen,
revision restore, cycle rejection, unsaved navigation, concurrent-edit recovery
via copy, cancellation, supported local execution, authenticated reload and
mobile overflow. `scripts/verify-local-model.py --workflow` optionally exercises
the saved run against an already installed real local model with actual resource
admission; no model download or owner-profile mutation is performed.

Full16-node execution, automatic triggers, branch/condition/retry semantics,
general approval/reply/publishing integration and broad multilingual/hardware
quality acceptance remain unfinished.
