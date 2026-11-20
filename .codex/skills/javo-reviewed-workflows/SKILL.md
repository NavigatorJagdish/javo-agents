---
name: javo-reviewed-workflows
description: Configure or debug Javo's scoped external-agent bridge, original n8n templates, reviewed local workflow proposals and optional creator models. Use for this repository's integrations, not general n8n or arbitrary agent installation.
---

Read the workspace's current `JAVO_PROJECT_MEMORY.md` and applicable repository
instructions first. Keep verified behavior separate from catalog/template entries.

Use `docs/CREATOR_AND_INTEGRATIONS.md` for current features and client paths,
`docs/N8N_WORKFLOWS.md` for node/credential setup, and
`docs/THIRD_PARTY_BOUNDARY.md` for distribution restrictions.

External clients use separate expiring scoped grants on
`/api/integrations/mcp`; do not put the owner token in an external tool, prompt,
workflow JSON or export. A proposal cannot approve/resume/publish/spend. Review
the exact saved graph/input in Javo and inspect the actual final run receipt.
After an uncertain submission, inspect the existing request key/receipt before
any retry. Approval is not completion.

Validate prepared n8n graphs with `node scripts/verify-n8n-templates.cjs` from
the checkout root. Report this as template contracts, not external engine
acceptance. Native Javo execution supports Trigger/local AI Prompt/Delay/Condition/Approval/End;
read `/api/workflows/node-types` before proposing any other node.
Conditions select a single data-only branch. Mid-run owner reviews bind the
actual draft/input/definition, release the worker and resume completed checkpoints
without replay. Scoped client tokens cannot decide these reviews.

Keep heavyweight agents/models in separate environments; start one at a time
on small hardware. Do not bypass runtime headroom/pause/emergency checks to
make acceptance pass. Use isolated temporary profiles for tests, never owner
databases or production credentials. Real speech acceptance uses
`scripts/verify-local-speech.py`; browser audio fixtures do not prove model
quality. Voice customization is not model training.

Keep Javo's MIT notice unchanged, retain third-party notices and keep restricted
n8n/Task Master/ComfyUI runtimes and model weights outside app/source bundles.
Never infer all commercial/model rights from a repository's headline license.
