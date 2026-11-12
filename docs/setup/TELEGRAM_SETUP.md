# Telegram Bot Remote Control Setup

Control Javo Agents, receive approval requests, and trigger Emergency Stop directly from Telegram.

## 1. Create Your Private Bot

1. Open Telegram and message **@BotFather**.
2. Send `/newbot` and follow the prompts to name your bot (e.g., `MyJavoCreatorBot`).
3. Copy the **HTTP API Bot Token** provided by `@BotFather`.

## 2. Find Your Numeric Telegram User ID

1. Message **@userinfobot** (or `@RawDataBot`) on Telegram to get your numeric `id` (e.g., `123456789`).
2. **Never leave the user allowlist empty** — only your numeric ID should be permitted to control your PC.

## 3. Configure Javo Agents

In **Dashboard → Integrations → Telegram** or `services/local-runtime/.env`:

```env
JAVO_TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
JAVO_TELEGRAM_ALLOWED_USERS=["123456789"]
```

## 4. Supported Commands

- `/status` — Show active agents, RAM/CPU usage, and pending approvals
- `/approvals` — List pending publish items with inline **Approve / Reject** buttons
- `/pause` — Pause Supervised Autopilot
- `/resume` — Resume Supervised Autopilot
- `/stop` — Trigger **Emergency Stop** immediately
- `/goal <text>` — Create a quick creator goal or draft task
