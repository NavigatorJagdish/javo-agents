# Voice Mode & 16-Node Visual Workflows Guide

## 1. Using Voice Mode (English, Hindi & Hinglish)

Voice Mode lets you talk naturally to your Master Orchestrator on Windows or Android:
- *"Nayi YouTube Short ke liye 5 Hinglish hooks likho aur approval queue mein daalo."*
- *"Show me today's pending approvals and pause publishing for Facebook."*

### Waveform States
- **Idle**: Gentle cyan-violet ambient pulse
- **Listening**: Reactive cyan bars capturing speech via `whisper.cpp`
- **Thinking**: Violet-dominant shimmer while Orchestrator + specialist agents plan
- **Executing**: Rapid dual-tone bars during local skill/draft execution
- **Finished**: Calm confirmation chime via `Piper` TTS

---

## 2. Building Visual Workflows (16 Node Types)

The Workflow Builder (`apps/dashboard` + `packages/workflow-schema`) supports **16 validated node types**:

| Category | Node Types |
| :--- | :--- |
| **Triggers** | `trigger`, `schedule`, `folder_watcher`, `account_event` |
| **AI & Analysis** | `content_analyzer`, `ai_prompt` |
| **Logic & Control** | `condition`, `approval`, `delay`, `retry`, `error_handler` |
| **Actions** | `publish`, `comment_reply`, `notification`, `analytics` |
| **Terminal** | `end` |

### Recommended Creator Pipeline
```
folder_watcher (Raw Videos)
  → content_analyzer (Transcript + Tags)
  → ai_prompt (Hinglish Hooks + Caption)
  → approval (Desktop + Android Push)
  → publish (YouTube Shorts / IG Reels)
  → notification (Telegram Summary)
  → end
```

> [!TIP]
> Under **Supervised Autopilot**, any workflow containing `publish` or `comment_reply` without an upstream `approval` node triggers a validation warning and automatically routes to your Approval Inbox before posting.
