# Durable supported specialist operations

The AI Team page reads registered definitions and saved executions from the
runtime. It no longer displays sample success percentages, completed-task
counts or model assignments. Registration/enabled state does not certify a
module's full functionality. The available-operation list is authoritative.

Initially supported operations are local reads:

- Budget Guardian: saved usage summary and the current budget-policy check.
- Goal Persistence: a real owner-scoped saved goal/evidence/milestone summary.

They do not call a model, post to a platform, execute arbitrary downloaded code,
generate experiments or authorize spending. Other specialist run requests return
501 until their execution path is completed and reviewed. The Master
Orchestrator and other source definitions remain under development.

`POST /agents/{key-or-id}/run` accepts `task_data` and an optional linked
`task_id`. It returns a queued receipt, not a completed result. Supported inputs
are strictly validated. The owner API generates a bounded read-permission
snapshot; a caller cannot inject arbitrary grants or cost receipts. The queue
is persisted and its admission bound is enforced in a SQLite immediate
transaction. A task cannot have two simultaneously active executions.

The worker holds an OS-backed lease for its runtime database, so a second
dispatcher cannot mistake a live execution for a crashed process. Queued work
survives restart and waits while the runtime is paused/stopped or resources
are insufficient. One dispatcher executes supported operations sequentially
through the existing bounded resource manager, with a 30-second lifetime.
Task deadlines, agent enabled state, permissions and controls are checked again.
An in-progress marker after a process restart becomes failed and requires an
explicit rerun; it is never silently called successful or blindly replayed.

Execution results are persisted separately from task metadata. Associated tasks
become running/completed only after actual worker transitions. Their history
records queue/start/outcome. A task's active inputs and recorded results cannot
be silently overwritten through metadata edits. Goal removal retains task
history; task removal cancels and detaches its execution receipts.

`GET /agents/{key-or-id}/executions` lists recent receipts; the execution-ID
detail endpoint returns saved input/authorization/output, timestamps and state.
`POST .../executions/{execution-id}/cancel` persists cancellation and requests
cooperative interruption. Emergency stop uses the existing shared controls.
Conditional completion prevents a late result from overwriting cancellation.
The worker also classifies emergency-stop interruption as cancelled before the
control endpoint finishes its database updates. A forced delayed-control test
covers that race, including when the worker finishes recording first.
The UI presents readable goal/budget results and explicit unavailable/error
states. It does not replace failed calls with prototype data.

On upgrade, code-owned registry metadata is refreshed while owner enable/disable
choices, saved agent configuration and execution history are preserved.

Windows desktop shutdown now terminates the exact owned backend process tree
and awaits confirmation. Stopping only a venv launcher can leave its interpreter
and HTTP listener behind. The separate smoke harness uses the same process-tree
principle for its temporary runtime. This does not claim graceful completion of
arbitrary in-flight remote operations. The worker records interruptions on the
next startup. Port zero now allocates and reports a real service port.

Tests cover real HTTP/database queueing, restart, linked task results,
unsupported/disabled requests, bounded concurrent admission, cancellation and
emergency stop, revoked task permissions, missed deadlines, task deletion and
registry/config preservation. OS-lock tests use a separate process. Windows
desktop tests include a real launcher plus HTTP grandchild and prove both stop.
The browser scenario exercises actual queue/worker/results/reload. Local source
browser tests use synthetic available-resource metrics to avoid depending on
other apps' RAM usage; the frozen Windows CI scenario uses actual runner metrics.
Neither is a minimum-hardware, full-specialist, live-social or release certification.
