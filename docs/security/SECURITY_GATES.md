# Security Gates & Supervised Autopilot Rules

Javo Agents enforces deterministic security gates via `packages/policy-engine/src/index.ts` and `services/local-runtime/app/core/security.py`.

## 1. Autopilot Modes

| Mode | Read / Analyze | Generate Drafts | Schedule | Publish / Reply | Skill Install |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `read_only_observer` | Allowed | Denied | Denied | Denied | Denied |
| `supervised_autopilot` *(Default)* | Allowed | Allowed | Allowed | **Human Approval** | **Human Approval** |
| `paused` | Denied | Denied | Denied | Denied | Denied |

## 2. Permission Scopes

Every agent and workflow action checks least-privilege scopes:
- `read:content`, `write:draft`
- `filesystem:read`, `filesystem:write`
- `publish:social`, `reply:comments`
- `execute:skill`
- `ai:local`, `ai:cloud`
- `network:external`, `secrets:read`

## 3. Emergency Stop (Kill Switch)

Triggering Emergency Stop immediately:
1. Halts all running tasks and workflow executions.
2. Sets `emergency_stop_active = true` across the API, Windows Tray, and Android Companion.
3. Blocks all `evaluatePolicy()` calls with `decision: "deny"` until explicitly resumed by the owner.

## 4. Zero-Cost & Budget Guardrails

- When `zeroCostOnly = true`, any action with `estimatedCostUsd > 0` is denied automatically.
- When `dailySpendUsd + estimatedCostUsd > dailyBudgetUsd` or monthly cap is reached, cloud AI calls are blocked and recommended back to local `ollama`.
