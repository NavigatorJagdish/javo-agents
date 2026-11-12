## Summary
Describe the changes made in this PR and why they are needed.

## Checklist
- [ ] Shared types (`packages/shared-types`) align with `services/local-runtime` models
- [ ] No secrets, `.env` files, or API keys are committed
- [ ] Destructive/external actions respect Supervised Autopilot approval gates
- [ ] Relevant tests pass locally:
  - [ ] `python -m unittest skills/tests/test_sandbox.py`
  - [ ] `tsc` on modified TypeScript packages / apps
