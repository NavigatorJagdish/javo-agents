"""Multi-provider AI routing with budget enforcement and usage tracking."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx

from app.config import get_settings
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
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageTracker:
    daily_spend_usd: float = 0.0
    monthly_spend_usd: float = 0.0
    total_requests: int = 0
    total_tokens: int = 0
    last_reset_day: str = ""
    last_reset_month: str = ""
    provider_counts: dict[str, int] = field(default_factory=dict)

    def maybe_reset(self) -> None:
        now = datetime.now(timezone.utc)
        day_str = now.strftime("%Y-%m-%d")
        month_str = now.strftime("%Y-%m")
        if self.last_reset_day != day_str:
            self.daily_spend_usd = 0.0
            self.last_reset_day = day_str
        if self.last_reset_month != month_str:
            self.monthly_spend_usd = 0.0
            self.last_reset_month = month_str


# Approximate USD cost per 1K tokens
MODEL_COSTS_PER_1K: dict[str, tuple[float, float]] = {
    "ollama": (0.0, 0.0),
    "gemini-2.0-flash": (0.0001, 0.0004),
    "gemini-1.5-flash": (0.000075, 0.0003),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
}


class AIRouter:
    """Routes AI requests across Ollama, Gemini, and OpenAI-compatible providers."""

    def __init__(self):
        self.usage = UsageTracker()
        self._provider_overrides: dict[str, dict[str, Any]] = {}

    def configure_provider(self, provider: str, config: dict[str, Any]) -> None:
        """Update runtime configuration for an AI provider."""
        self._provider_overrides[provider] = {
            **self._provider_overrides.get(provider, {}),
            **config,
        }
        logger.info("Configured AI provider override for %s", provider)

    def get_provider_status(self) -> dict[str, Any]:
        """Return configured providers and usage metrics."""
        settings = get_settings()
        self.usage.maybe_reset()
        return {
            "default_provider": settings.default_ai_provider,
            "providers": {
                "ollama": {
                    "enabled": True,
                    "base_url": self._provider_overrides.get("ollama", {}).get(
                        "base_url", settings.ollama_base_url
                    ),
                    "model": self._provider_overrides.get("ollama", {}).get(
                        "model", settings.ollama_default_model
                    ),
                    "local": True,
                },
                "gemini": {
                    "enabled": bool(
                        self._provider_overrides.get("gemini", {}).get("api_key")
                        or settings.gemini_api_key
                    ),
                    "model": self._provider_overrides.get("gemini", {}).get(
                        "model", settings.gemini_model
                    ),
                    "local": False,
                },
                "openai": {
                    "enabled": bool(
                        self._provider_overrides.get("openai", {}).get("api_key")
                        or settings.openai_api_key
                    ),
                    "base_url": self._provider_overrides.get("openai", {}).get(
                        "base_url", settings.openai_base_url
                    ),
                    "model": self._provider_overrides.get("openai", {}).get(
                        "model", settings.openai_model
                    ),
                    "local": False,
                },
            },
            "usage": {
                "daily_spend_usd": round(self.usage.daily_spend_usd, 6),
                "monthly_spend_usd": round(self.usage.monthly_spend_usd, 6),
                "daily_budget_usd": settings.ai_daily_budget,
                "monthly_budget_usd": settings.ai_monthly_budget,
                "total_requests": self.usage.total_requests,
                "total_tokens": self.usage.total_tokens,
                "provider_counts": self.usage.provider_counts,
            },
        }

    def _check_budget(self, provider: str) -> None:
        settings = get_settings()
        self.usage.maybe_reset()
        if provider == AIProvider.OLLAMA.value:
            return  # Local inference is zero-cost
        if self.usage.daily_spend_usd >= settings.ai_daily_budget:
            raise RuntimeError(
                f"Daily AI budget exceeded (${self.usage.daily_spend_usd:.4f} / ${settings.ai_daily_budget:.2f})"
            )
        if self.usage.monthly_spend_usd >= settings.ai_monthly_budget:
            raise RuntimeError(
                f"Monthly AI budget exceeded (${self.usage.monthly_spend_usd:.4f} / ${settings.ai_monthly_budget:.2f})"
            )

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int, provider: str) -> float:
        if provider == AIProvider.OLLAMA.value:
            return 0.0
        in_rate, out_rate = MODEL_COSTS_PER_1K.get(model, (0.0005, 0.0015))
        return (prompt_tokens / 1000.0) * in_rate + (completion_tokens / 1000.0) * out_rate

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
        settings = get_settings()
        chosen_provider = provider or settings.default_ai_provider
        max_tok = max_tokens or settings.max_tokens_per_request

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
            else:
                raise

        start = time.perf_counter()
        try:
            if chosen_provider == AIProvider.OLLAMA.value:
                resp = await self._call_ollama(
                    sanitized_prompt, sanitized_system, model, temperature, max_tok
                )
            elif chosen_provider == AIProvider.GEMINI.value:
                resp = await self._call_gemini(
                    sanitized_prompt, sanitized_system, model, temperature, max_tok
                )
            elif chosen_provider == AIProvider.OPENAI.value:
                resp = await self._call_openai(
                    sanitized_prompt, sanitized_system, model, temperature, max_tok
                )
            else:
                raise ValueError(f"Unsupported AI provider: {chosen_provider}")
        except Exception as exc:
            if fallback_to_local and chosen_provider != AIProvider.OLLAMA.value:
                logger.warning("Provider %s failed (%s); falling back to ollama", chosen_provider, exc)
                resp = await self._call_ollama(
                    sanitized_prompt, sanitized_system, None, temperature, max_tok
                )
            else:
                raise

        resp.latency_ms = round((time.perf_counter() - start) * 1000, 2)
        self._record_usage(resp)
        return resp

    def _record_usage(self, resp: AIResponse) -> None:
        self.usage.maybe_reset()
        self.usage.total_requests += 1
        self.usage.total_tokens += resp.total_tokens
        self.usage.daily_spend_usd += resp.cost_usd
        self.usage.monthly_spend_usd += resp.cost_usd
        self.usage.provider_counts[resp.provider] = (
            self.usage.provider_counts.get(resp.provider, 0) + 1
        )

    async def _call_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AIResponse:
        settings = get_settings()
        override = self._provider_overrides.get("ollama", {})
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
        prompt_tokens = int(data.get("prompt_eval_count", 0))
        completion_tokens = int(data.get("eval_count", 0))
        return AIResponse(
            content=content,
            provider=AIProvider.OLLAMA.value,
            model=chosen_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=0.0,
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
        override = self._provider_overrides.get("gemini", {})
        api_key = override.get("api_key") or settings.gemini_api_key
        if not api_key:
            raise RuntimeError("Gemini API key is not configured")
        chosen_model = model or override.get("model", settings.gemini_model)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{chosen_model}:generateContent?key={api_key}"
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
            res = await client.post(url, json=body)
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
        override = self._provider_overrides.get("openai", {})
        api_key = override.get("api_key") or settings.openai_api_key
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
        base_url = self._provider_overrides.get("ollama", {}).get(
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
