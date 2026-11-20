# Reviewed n8n and native workflow setup

Javo supplies original inactive JSON templates. n8n remains a separately operated
external service; it is not a Javo dependency or bundled MIT component.
These templates passed structure and JavaScript contract tests, not an actual
n8n import/execution acceptance run.

1. Save a supported manual local workflow in Javo. Available templates are caption,
   Hindi voice script and ideas from supplied source-labelled trends.
2. In Integrations, create an `n8n` grant with `read_status`, `read_workflows`,
   `propose_workflow` and `read_own_results`. Use a short expiry.
3. In your separate n8n instance, import
   `integrations/n8n-reviewed-drafting.json`, retaining its inactive state.
4. Create an HTTP Header Auth credential named as you choose. Header name is
   `Authorization`; value is `Bearer ` followed by the new client token. Select
   that credential on all five HTTP Request nodes. Never paste the owner token
   or a credential into a Code node, expression, export or workflow JSON.
5. Set the saved workflow UUID, loopback Javo URL and verified brief in Set brief.
   `127.0.0.1` means the n8n host; a container/remote host cannot reach Javo through
   its own loopback. This template deliberately does not expose Javo on a LAN.
6. Run manually. Open Javo Review inbox, inspect the exact graph/prompts/input and
   approve or reject. Resume Javo separately only when ready to execute.
7. Inspect the actual run and returned result. A timeout retains the existing
   proposal/run receipt; inspect it instead of creating an automatic replacement.

The17 nodes include manual/disabled schedule starts, brief input, validation,
saved revision selection, proposal submission, durable reference, wait/status
polling, completed/eligible branches, actual result fetch, verified report,
stop-without-replay and sanitized failure output. Polling is capped at30×10seconds
plus request time. It uses the per-execution zero-based `$runIndex`, described in
the [official metadata reference](https://github.com/n8n-io/n8n-docs/blob/main/docs/build/code-in-n8n/use-built-in-shortcuts/n8n-metadata.md).
Wait behavior follows the [official Wait node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/).
The scheduled trigger stays disabled pending separate operator review. Reads are
limited to the first20 saved workflow summaries; choose a listed workflow.

The smaller `integrations/n8n-read-status.json` performs a manual read only.
Regenerate and check the reviewed template from the repository root:

```powershell
python scripts/build-n8n-templates.py
node scripts/verify-n8n-templates.cjs
```

Native Javo exposes16 node definitions with honest execution availability through
`/api/workflows/node-types`. Only Trigger, local AI Prompt, Delay and End execute
today. Other types can be saved for planning and are rejected before enqueue.
Native branches, retries, automatic triggers, approval nodes, voice/media nodes
and live publishing require implementation and independent acceptance. The n8n
template's control nodes do not make those native Javo nodes executable.
