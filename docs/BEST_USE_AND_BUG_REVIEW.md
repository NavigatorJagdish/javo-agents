# Best use and realistic-use bug review — 18 November 2026

This is an implementation/use review, not a claim to have monitored real
production users. No production telemetry or external-user session was available.
Repository issues contain reported Android/device/OAuth needs; reproduced local
failures and recommendations below are kept separate from those reports.

## Best use of the current build

1. Check actual hardware measurements and local model inventory in setup or
   Settings. Save a compatible installed model, keep cloud budgets disabled,
   and leave free OS memory. A model appearing in a list is not a generation test.
2. Save local account records and their individual brand voice/audience/pillars.
   They are unconnected planning records until official OAuth is implemented;
   do not enter platform passwords or tokens into prompts/configuration.
3. Use the caption draft template for a reviewed local workflow: manual start,
   one local AI drafting step, End. Put a short brief in the prompt/trigger data,
   save, review its revision, then explicitly run. Read and edit the output.
   Account brand rules are not automatically imported into this workflow yet;
   include the intended nonsecret rules in the brief yourself.
4. Record a source-labelled baseline/target in Goals and update observations
   manually from actual reports. Treat growth expectations as objectives,
   not guaranteed outcomes or automatically verified analytics.
5. Use Content to import original files and inspect an exact preview. Review
   the actual caption/destination before approving a simulation. A simulation
   receipt never means a real social post was sent.
6. If a graph changes in another tab/session, keep the local edits and save a
   separate copy, or explicitly reload the saved version. Restore older revisions
   when needed. Check the revision on each run receipt: editing the graph does
   not change an already queued, reviewed snapshot.
7. Keep the runtime resumed only when eligible work should proceed. Pause holds
   between workflow nodes; cancel prevents a specific queued/running job from
   completing. Emergency stop is broader. After restart, review interrupted
   receipts and explicitly run again rather than assuming success.
8. When memory is busy, close unused applications or unload an idle model and
   retry. Do not weaken admission guards to force inference. A saved workflow
   may remain queued while resources are unavailable and can expire; it has
   not completed merely because it was accepted into the queue.

Small local models are useful for short, supervised drafts. Independently check
facts, language quality and brand fit. Speech, autonomous account management and
full visual automation remain incomplete; manual review is still necessary.

## Reproduced problems and changes

| Observed failure or user mistake | Repair |
| --- | --- |
| Editor sends ReactFlow objects to a different server schema | Actual mapping, real saved graph reopening and visible server errors |
| Reload loses the editor's apparent saved graph | Runtime-backed selection/reopen and revision history |
| Newly saved graph briefly disappears from the selector while list refresh lags | Retain the confirmed current graph as an option, including when outside the current list page |
| A second tab silently overwrites a newer graph | Expected-revision checks,409conflict, preserved edits and Save as new copy |
| Reusing node IDs across workflows collides with database keys | Owner/graph ID checks; copies generate new node and edge IDs |
| Circular/dangling/duplicate connections can be saved | Client cycle prevention plus server graph validation before any mutation |
| Invalid numbers inside arbitrary configuration normalize before validation | Validate original finite JSON before serialization; reject without partial save |
| Unsaved edits disappear when switching pages or loading another graph | Route/reload warnings and explicit discard confirmations |
| Phone-width resize clips the graph to its first node | Refit on resize; executable nodes are separate from save-only planning nodes |
| Workflow animation/records imply execution without a worker | Actual supported worker, fixed reviewed snapshots, node logs and truthful queued/running/final receipts |
| Cancel/stop or restart could be mistaken for completion | Conditional finalization, actual cooperative cancellation, no blind interrupted-run replay and retained history |
| Old prototype counters imply verified runs | Count new completed receipts separately; legacy receipts are labelled unverified |
| Busy local inference returns a generic provider failure | Actionable memory/queue guidance, no provider-detail leakage and unchanged safeguards |

The wider timer test also exposed a valid transient receipt (`dispatching`) between
durable commits. Its polling assertion now waits for both the final simulated
receipt and final timer state, while rejecting unknown/failed states and retaining
the completion deadline. The production API continues to report honest in-flight
state; an in-flight record is not hidden or treated as success.

## Reported needs that are not current-device verification

[Issue3](https://github.com/NavigatorJagdish/javo-agents/issues/3) requests real
Android standalone acceptance, including repeated Hindi/Hinglish/English voice,
speech-recognizer errors11/13, interruption, drafts and tasks. Those phone
observations were not reproduced on this Windows host. Physical-device testing
is still required; automated CI is not owner-device acceptance.
[Issue4](https://github.com/NavigatorJagdish/javo-agents/issues/4) requests official
mobile OAuth and verified account capabilities; registrations/permissions and
an explicitly approved deployment remain prerequisites. Historical CI issue2
is not proof that current Windows/backend checks fail.

## Recommended next improvements

1. Complete the shared approval policy and one official social path, with actual
   account capability checks, exact reviewed content and remote receipt verification.
2. Extend workflow node support only when each node has real bounded execution,
   permissions, cancellation/recovery and failure evidence; keep unsupported
   nodes explicit instead of substituting simulated success.
3. Finish full encrypted profile recovery, then Android/Telegram pairing and
   physical-device speech acceptance. Keep optional hosted execution and any
   paid activation separate, explicit decisions.
4. Add multilingual model quality and sustained8GB/larger-hardware benchmarks,
   complete accessibility/design-reference review and signed release acceptance.

The complete ecosystem remains unfinished. See CURRENT_DELIVERY_REVIEW.md for
the remaining scope and WORKFLOWS.md for exact current workflow boundaries.
