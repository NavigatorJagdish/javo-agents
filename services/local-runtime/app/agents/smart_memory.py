"""Smart Memory agent — stores/retrieves contextual memory and learns user preferences."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class SmartMemoryAgent(BaseAgent):
    """Specialist agent for contextual memory retrieval, storage, and preference learning."""

    name = "smart_memory"
    display_name = "Smart Memory"
    description = "Stores and retrieves contextual memories, user preferences, and learned interaction patterns."
    version = "1.0.0"
    capabilities = ["memory_store", "memory_retrieve", "preference_learning", "context_recall"]
    required_permissions = ["read_memory", "write_memory"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "key": {"type": "string"},
            "content": {"type": "string"},
            "query": {"type": "string"},
            "tags": {"type": "array"},
            "importance": {"type": "number"},
        },
    }
    output_schema = {"required": ["status"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()
        self._memory_store: list[dict[str, Any]] = []
        self._preferences: dict[str, Any] = {}

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "retrieve")
        if action == "store":
            return self._store_memory(task_data)
        if action == "learn_preference":
            return self._learn_preference(task_data)
        if action == "summarize":
            return await self._summarize_memories(task_data)
        return self._retrieve_memory(task_data)

    def _store_memory(self, task_data: dict) -> dict:
        entry = {
            "id": f"mem_{len(self._memory_store) + 1}",
            "key": task_data.get("key", "general"),
            "content": task_data.get("content", ""),
            "tags": task_data.get("tags", []),
            "importance": float(task_data.get("importance", 0.5)),
            "created_at": time.time(),
            "access_count": 0,
        }
        self._memory_store.append(entry)
        self.logger.info("Stored memory %s (key=%s)", entry["id"], entry["key"])
        return {"status": "success", "memory": entry, "total_memories": len(self._memory_store)}

    def _retrieve_memory(self, task_data: dict) -> dict:
        query = task_data.get("query", "").lower()
        tags = set(task_data.get("tags", []))
        limit = int(task_data.get("limit", 10))

        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in self._memory_store:
            score = entry["importance"]
            if query and query in entry["content"].lower():
                score += 2.0
            if query and query in entry["key"].lower():
                score += 1.5
            if tags:
                overlap = len(tags.intersection(set(entry["tags"])))
                score += overlap * 1.2
            if not query and not tags:
                score += 0.1
            if score > entry["importance"] or (not query and not tags):
                scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        matches = []
        for score, entry in scored[:limit]:
            entry["access_count"] += 1
            matches.append({**entry, "relevance_score": round(score, 2)})

        return {"status": "success", "matches": matches, "count": len(matches), "preferences": self._preferences}

    def _learn_preference(self, task_data: dict) -> dict:
        pref_key = task_data.get("key", "")
        pref_val = task_data.get("value")
        if not pref_key:
            return {"status": "error", "error": "Preference key is required"}
        self._preferences[pref_key] = {"value": pref_val, "updated_at": time.time()}
        return {"status": "success", "preference": {pref_key: pref_val}, "total_preferences": len(self._preferences)}

    async def _summarize_memories(self, task_data: dict) -> dict:
        recent = self._memory_store[-20:]
        snippet = "\n".join(f"- [{m['key']}] {m['content']}" for m in recent)
        if not snippet:
            return {"status": "success", "summary": "No memories stored yet.", "tokens_used": 0}
        summary, tokens = await self.ask_ai(
            self.ai_router,
            f"Summarize key facts from these memories:\n{snippet}",
            fallback=f"Stored {len(self._memory_store)} memories.",
        )
        return {"status": "success", "summary": summary, "tokens_used": tokens}
