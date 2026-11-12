"""Telegram Agent — handles Telegram bot commands, notifications, and approvals."""

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class TelegramAgent(BaseAgent):
    """Specialist agent for Telegram bot command parsing, notifications, and remote control."""

    name = "telegram_agent"
    display_name = "Telegram Bot Agent"
    description = "Handles incoming Telegram bot commands, formats notifications, and dispatches interactive approval prompts."
    version = "1.0.0"
    capabilities = ["telegram_commands", "send_notification", "remote_control", "approval_prompt"]
    required_permissions = ["telegram_send", "read_status"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "chat_id": {"type": "string"},
            "message": {"type": "string"},
            "command": {"type": "string"},
        },
    }
    output_schema = {"required": ["status"]}

    SUPPORTED_COMMANDS = {
        "/status": "Return runtime health and active tasks summary",
        "/pause": "Pause automated publishing and scheduled tasks",
        "/resume": "Resume paused schedules",
        "/stop": "Trigger emergency stop for running tasks",
        "/approvals": "List items awaiting human approval",
        "/help": "List available bot commands",
    }

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "handle_command")
        if action == "send_notification":
            return self._prepare_notification(task_data)
        if action == "send_approval":
            return self._prepare_approval_keyboard(task_data)
        return self._handle_command(task_data)

    def _handle_command(self, task_data: dict) -> dict:
        raw_cmd = task_data.get("command", "/help").strip()
        cmd = raw_cmd.split()[0].lower()
        chat_id = str(task_data.get("chat_id", ""))

        if cmd not in self.SUPPORTED_COMMANDS:
            return {
                "status": "success",
                "chat_id": chat_id,
                "recognized": False,
                "reply_text": f"Unknown command '{cmd}'. Send /help for available commands.",
            }

        if cmd == "/help":
            lines = [f"{k} — {v}" for k, v in self.SUPPORTED_COMMANDS.items()]
            reply = "Javo Agents Bot Commands:\n" + "\n".join(lines)
        elif cmd == "/stop":
            reply = "Emergency stop signal queued. All active non-essential tasks will halt."
        elif cmd == "/pause":
            reply = "Autopilot schedules paused."
        elif cmd == "/resume":
            reply = "Autopilot schedules resumed."
        elif cmd == "/approvals":
            reply = "Checking pending approvals queue..."
        else:
            reply = "System status: Local runtime online. Send /approvals to inspect pending items."

        return {
            "status": "success",
            "chat_id": chat_id,
            "recognized": True,
            "command": cmd,
            "reply_text": reply,
        }

    def _prepare_notification(self, task_data: dict) -> dict:
        chat_id = str(task_data.get("chat_id", ""))
        title = task_data.get("title", "Javo Agents")
        message = task_data.get("message", "")
        formatted = f"*{title}*\n{message}".strip()
        return {
            "status": "success",
            "queued": bool(chat_id),
            "chat_id": chat_id,
            "formatted_message": formatted,
            "parse_mode": "Markdown",
        }

    def _prepare_approval_keyboard(self, task_data: dict) -> dict:
        item_id = task_data.get("item_id", "unknown")
        summary = task_data.get("summary", "Action requires your approval")
        keyboard: dict[str, Any] = {
            "inline_keyboard": [[
                {"text": "Approve", "callback_data": f"approve:{item_id}"},
                {"text": "Reject", "callback_data": f"reject:{item_id}"},
            ]]
        }
        return {
            "status": "success",
            "chat_id": str(task_data.get("chat_id", "")),
            "text": f"Approval Request ({item_id}):\n{summary}",
            "reply_markup": keyboard,
        }
