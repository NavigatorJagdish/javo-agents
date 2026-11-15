"""Multi-provider AI routing with budget enforcement and usage tracking."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4
from enum import Enum
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.core.usage_ledger import UsageLedger
from app.services import provider_settings
from app.core.privacy_firewall import DataClassification, get_privacy_firewall

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None
    usage_reported: bool = False
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


class AIRouter:
    """Routes AI requests across Ollama, Gemini, and OpenAI-compatible providers."""

    def __init__(self):
        pass  # Accounting is shared through the durable profile ledger.

    def configure_provider(self, provider: str, config: dict[str, Any]) -> None:
        """Persist configuration using the same policy as the owner API."""
        provider_settings.update_provider(provider, config)

    def _ledger(self) -> UsageLedger:
        settings = provider_settings.get_settings()
        path = settings.usage_ledger_path or str(Path(settings.provider_config_path).with_name('usage-ledger.sqlite'))
        return UsageLedger(path)

    def get_provider_status(self) -> dict[str, Any]:
        settings = provider_settings.effective()["settings"]
        providers = {item["name"]: {**item, "local": item["name"] == "ollama"}
                     for item in provider_settings.metadata()}
        usage = self._ledger().summary()
        usage.update(daily_budget_usd=settings["ai_daily_budget"], monthly_budget_usd=settings["ai_monthly_budget"])
        return {"default_provider": settings["default_ai_provider"], "providers": providers, "usage": usage}

    def _check_budget(self, provider: str) -> None:
        if provider == AIProvider.OLLAMA.value:
            return
        # Configuration/environment values are not authorization to spend. No
        # current price schedule or paid activation has been approved/verified.
        raise RuntimeError("Cloud budget execution is disabled pending verified pricing and explicit paid authorization")

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int, provider: str) -> float | None:
        return 0.0 if provider == AIProvider.OLLAMA.value else None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        classification: DataClassification = DataClassification.INTERNAL,
        fallback_to_local: bool = True,
    ) -> AIResponse:
        """Route a text generation request with privacy firewall and budget checks."""
        settings = provider_settings.effective()["settings"]
        chosen_provider = provider or settings["default_ai_provider"]
        if chosen_provider not in provider_settings.PROVIDERS:
            raise ValueError("Unsupported AI provider")
        chosen_model = model
        if max_tokens is not None and (isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1):
            raise ValueError("Requested max tokens must be a positive integer")
        max_tok = min(max_tokens or settings["max_tokens_per_request"], settings["max_tokens_per_request"])

        # Enforce privacy firewall before egress
        firewall = get_privacy_firewall()
        decision = firewall.evaluate_egress(
            data=f"{system_prompt or ''}\n{prompt}",
            provider=chosen_provider,
            classification=classification,
        )
        if not decision.allowed:
            if fallback_to_local and chosen_provider != AIProvider.OLLAMA.value:
                logger.warning(
                    "Privacy firewall blocked %s (%s); falling back to local ollama",
                    chosen_provider,
                    decision.reason,
                )
                chosen_provider = AIProvider.OLLAMA.value
                chosen_model = None
            else:
                raise PermissionError(f"Privacy firewall blocked AI egress: {decision.reason}")

        sanitized_prompt = firewall.redact_pii(prompt) if decision.should_redact else prompt
        sanitized_system = (
            firewall.redact_pii(system_prompt)
            if system_prompt and decision.should_redact
            else system_prompt
        )

        # Enforce budget
        try:
            self._check_budget(chosen_provider)
        except RuntimeError:
            if fallback_to_local and chosen_provider != AIProvider.OLLAMA.value:
                logger.warning("Budget exceeded for %s; falling back to local ollama", chosen_provider)
                chosen_provider = AIProvider.OLLAMA.value
                chosen_model = None
            else:
                raise

        config = self._provider_config(chosen_provider)
        request_id = str(uuid4())
        ledger = self._ledger()
        # Persist intent before any provider call. A storage failure prevents
        # inference; no process-local counter can replace the durable record.
        if not ledger.reserve(request_id, chosen_provider, chosen_model or config["model"]):
            raise RuntimeError("AI request ID is already recorded; duplicate dispatch blocked")
        start = time.perf_counter()
        try:
            if chosen_provider == AIProvider.OLLAMA.value:
                resp = await self._call_ollama(
                    sanitized_prompt, sanitized_system, chosen_model, temperature, max_tok
                )
            elif chosen_provider == AIProvider.GEMINI.value:
                resp = await self._call_gemini(
                    sanitized_prompt, sanitized_system, chosen_model, temperature, max_tok
                )
            elif chosen_provider == AIProvider.OPENAI.value:
                resp = await self._call_openai(
                    sanitized_prompt, sanitized_system, chosen_model, temperature, max_tok
                )
            else:
                raise ValueError("Unsupported AI provider")
        except (Exception, asyncio.CancelledError):
            ledger.fail(request_id)
            raise
        resp.latency_ms = round((time.perf_counter() - start) * 1000, 2)
        # Cloud execution is deliberately disabled. The supported local API
        # charge is known zero; missing token counts remain explicitly unknown.
        ledger.settle(request_id, prompt_tokens=resp.prompt_tokens if resp.usage_reported else None,
                      completion_tokens=resp.completion_tokens if resp.usage_reported else None,
                      cost_microusd=0)
        return resp

    def _provider_config(self, provider: str) -> dict:
        config = provider_settings.effective()["providers"][provider]
        if not config["enabled"]:
            raise RuntimeError("Selected AI provider is disabled")
        provider_settings._validate_url(provider, config["base_url"])
        return config

    async def _call_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AIResponse:
        settings = get_settings()
        override = self._provider_config("ollama")
        base_url = override.get("base_url", settings.ollama_base_url).rstrip("/")
        chosen_model = model or override.get("model", settings.ollama_default_model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": chosen_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{base_url}/api/chat", json=payload)
            res.raise_for_status()
            data = res.json()

        content = data.get("message", {}).get("content", "")
        usage_reported = all(isinstance(data.get(key), int) and not isinstance(data[key], bool)
                             and 0 <= data[key] <= 10**15 for key in ("prompt_eval_count", "eval_count"))
        prompt_tokens = data["prompt_eval_count"] if usage_reported else 0
        completion_tokens = data["eval_count"] if usage_reported else 0
        return AIResponse(
            content=content,
            provider=AIProvider.OLLAMA.value,
            model=chosen_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=0.0,
            usage_reported=usage_reported,
            raw=data,
        )

    async def _call_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AIResponse:
        settings = get_settings()
        self._check_budget("gemini")
        override = self._provider_config("gemini")
        api_key = override.get("api_key")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured")
        chosen_model = model or override.get("model", settings.gemini_model)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{chosen_model}:generateContent"
        )
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, json=body, headers={"x-goog-api-key": api_key})
            res.raise_for_status()
            data = res.json()

        candidates = data.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        content = "".join(p.get("text", "") for p in parts)
        usage_meta = data.get("usageMetadata", {})
        prompt_tokens = int(usage_meta.get("promptTokenCount", 0))
        completion_tokens = int(usage_meta.get("candidatesTokenCount", 0))
        cost = self._estimate_cost(chosen_model, prompt_tokens, completion_tokens, AIProvider.GEMINI.value)

        return AIResponse(
            content=content,
            provider=AIProvider.GEMINI.value,
            model=chosen_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            raw=data,
        )

    async def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AIResponse:
        settings = get_settings()
        self._check_budget("openai")
        override = self._provider_config("openai")
        api_key = override.get("api_key")
        if not api_key:
            raise RuntimeError("OpenAI API key is not configured")
        base_url = override.get("base_url", settings.openai_base_url).rstrip("/")
        chosen_model = model or override.get("model", settings.openai_model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        choices = data.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = data.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        cost = self._estimate_cost(chosen_model, prompt_tokens, completion_tokens, AIProvider.OPENAI.value)

        return AIResponse(
            content=content,
            provider=AIProvider.OPENAI.value,
            model=chosen_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            raw=data,
        )

    async def check_ollama_health(self) -> dict[str, Any]:
        """Check if local Ollama daemon is reachable and list loaded models."""
        settings = get_settings()
        base_url = self._provider_config("ollama").get(
            "base_url", settings.ollama_base_url
        ).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{base_url}/api/tags")
                res.raise_for_status()
                models = [m.get("name") for m in res.json().get("models", [])]
                return {"reachable": True, "models": models}
        except Exception as exc:
            return {"reachable": False, "error": str(exc), "models": []}


_ai_router: Optional[AIRouter] = None


def get_ai_router() -> AIRouter:
    """Get or create the AIRouter singleton."""
    global _ai_router
    if _ai_router is None:
        _ai_router = AIRouter()
    return _ai_router
