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
    """Routes AI requests across Ollama, Gemini, OpenAI, and custom OpenAI-compatible providers."""

    def __init__(self):
        self.usage = UsageTracker()
        self._provider_overrides: dict[str, dict[str, Any]] = {}
        self._custom_providers: dict[str, dict[str, Any]] = {}
        self._queued_jobs: list[dict[str, Any]] = []
        self._disabled_providers: set[str] = set()

    def configure_provider(self, provider: str, config: dict[str, Any]) -> None:
        """Update runtime configuration for a built-in or custom AI provider."""
        key = provider.lower()
        clean = dict(config)
        enabled = clean.pop("enabled", None)
        if enabled is False:
            self._disabled_providers.add(key)
        elif enabled is True:
            self._disabled_providers.discard(key)

        if key in {p.value for p in AIProvider}:
            self._provider_overrides[key] = {
                **self._provider_overrides.get(key, {}),
                **clean,
            }
        else:
            existing = self._custom_providers.get(
                key,
                {
                    "name": key,
                    "base_url": "",
                    "model": "default",
                    "api_key": None,
                    "local": False,
                },
            )
            existing.update(clean)
            if clean.get("base_url", "").startswith(("http://127.0.0.1", "http://localhost")):
                existing["local"] = True
            self._custom_providers[key] = existing
            firewall = get_privacy_firewall()
            if key not in firewall.provider_policies:
                firewall.update_policy(
                    key,
                    {
                        "local": bool(existing.get("local", False)),
                        "max_classification": (
                            DataClassification.RESTRICTED
                            if existing.get("local")
                            else DataClassification.INTERNAL
                        ),
                        "redact_pii": not bool(existing.get("local", False)),
                        "allow_egress": True,
                    },
                )
        logger.info("Configured AI provider override for %s", key)

    def remove_provider_key(self, provider: str) -> bool:
        """Remove an API key for a configured AI provider (and custom entry if requested)."""
        key = provider.lower()
        removed = False
        if key in self._provider_overrides and "api_key" in self._provider_overrides[key]:
            self._provider_overrides[key].pop("api_key", None)
            removed = True
        if key in self._custom_providers and self._custom_providers[key].get("api_key"):
            self._custom_providers[key]["api_key"] = None
            removed = True
        if key in {"gemini", "openai"}:
            self._disabled_providers.add(key)
        return removed

    def delete_custom_provider(self, provider: str) -> bool:
        """Delete a custom OpenAI-compatible provider entry."""
        key = provider.lower()
        existed = key in self._custom_providers
        self._custom_providers.pop(key, None)
        self._disabled_providers.discard(key)
        return existed

    def enqueue_offline_job(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Queue an AI job locally when all inference providers are unavailable."""
        job = {
            "job_id": f"aiq_{len(self._queued_jobs) + 1}_{int(time.time())}",
            "prompt": prompt,
            "system_prompt": system_prompt,
            "provider": provider or get_settings().default_ai_provider,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._queued_jobs.append(job)
        return job

    def get_queued_jobs(self) -> list[dict[str, Any]]:
        """Return queued AI jobs waiting for provider availability."""
        return list(self._queued_jobs)

    async def drain_queued_jobs(self, limit: int = 10) -> dict[str, Any]:
        """Attempt to execute queued jobs now that a provider may be reachable."""
        processed: list[dict[str, Any]] = []
        remaining: list[dict[str, Any]] = []
        for idx, job in enumerate(self._queued_jobs):
            if idx >= limit:
                remaining.append(job)
                continue
            try:
                resp = await self.generate(
                    prompt=job["prompt"],
                    system_prompt=job.get("system_prompt"),
                    provider=job.get("provider"),
                    fallback_to_local=True,
                )
                processed.append(
                    {
                        "job_id": job["job_id"],
                        "status": "completed",
                        "provider": resp.provider,
                        "model": resp.model,
                        "content": resp.content,
                    }
                )
            except Exception as exc:
                job["last_error"] = str(exc)
                remaining.append(job)
        self._queued_jobs = remaining
        return {
            "processed_count": len(processed),
            "remaining_count": len(remaining),
            "processed": processed,
        }

    def get_provider_status(self) -> dict[str, Any]:
        """Return configured providers and usage metrics."""
        settings = get_settings()
        self.usage.maybe_reset()
        providers: dict[str, dict[str, Any]] = {
            "ollama": {
                "enabled": "ollama" not in self._disabled_providers,
                "base_url": self._provider_overrides.get("ollama", {}).get(
                    "base_url", settings.ollama_base_url
                ),
                "model": self._provider_overrides.get("ollama", {}).get(
                    "model", settings.ollama_default_model
                ),
                "local": True,
                "has_api_key": False,
            },
            "gemini": {
                "enabled": (
                    "gemini" not in self._disabled_providers
                    and bool(
                        self._provider_overrides.get("gemini", {}).get("api_key")
                        or settings.gemini_api_key
                    )
                ),
                "model": self._provider_overrides.get("gemini", {}).get(
                    "model", settings.gemini_model
                ),
                "local": False,
                "has_api_key": bool(
                    self._provider_overrides.get("gemini", {}).get("api_key")
                    or settings.gemini_api_key
                ),
            },
            "openai": {
                "enabled": (
                    "openai" not in self._disabled_providers
                    and bool(
                        self._provider_overrides.get("openai", {}).get("api_key")
                        or settings.openai_api_key
                    )
                ),
                "base_url": self._provider_overrides.get("openai", {}).get(
                    "base_url", settings.openai_base_url
                ),
                "model": self._provider_overrides.get("openai", {}).get(
                    "model", settings.openai_model
                ),
                "local": False,
                "has_api_key": bool(
                    self._provider_overrides.get("openai", {}).get("api_key")
                    or settings.openai_api_key
                ),
            },
        }
        for name, cfg in self._custom_providers.items():
            providers[name] = {
                "enabled": name not in self._disabled_providers and bool(cfg.get("base_url")),
                "base_url": cfg.get("base_url", ""),
                "model": cfg.get("model", "default"),
                "local": bool(cfg.get("local", False)),
                "has_api_key": bool(cfg.get("api_key")),
                "custom": True,
            }
        return {
            "default_provider": settings.default_ai_provider,
            "providers": providers,
            "queued_jobs": len(self._queued_jobs),
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
            elif chosen_provider in self._custom_providers:
                resp = await self._call_custom(
                    chosen_provider, sanitized_prompt, sanitized_system, model, temperature, max_tok
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

    async def _call_custom(
        self,
        provider_name: str,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AIResponse:
        cfg = self._custom_providers[provider_name]
        base_url = str(cfg.get("base_url", "")).rstrip("/")
        if not base_url:
            raise RuntimeError(f"Custom provider '{provider_name}' is missing base_url")
        chosen_model = model or str(cfg.get("model", "default"))
        headers: dict[str, str] = {}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
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
        cost = (
            0.0
            if cfg.get("local")
            else self._estimate_cost(chosen_model, prompt_tokens, completion_tokens, provider_name)
        )
        return AIResponse(
            content=content,
            provider=provider_name,
            model=chosen_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            raw=data,
        )

    async def test_provider(self, provider: str) -> dict[str, Any]:
        """Test connectivity and credential readiness for a provider without wasting tokens."""
        key = provider.lower()
        settings = get_settings()
        if key == AIProvider.OLLAMA.value:
            health = await self.check_ollama_health()
            return {
                "provider": "ollama",
                "ok": bool(health.get("reachable")),
                "local": True,
                "models": health.get("models", []),
                "message": (
                    f"Ollama reachable ({len(health.get('models', []))} model(s))"
                    if health.get("reachable")
                    else f"Ollama offline: {health.get('error', 'connection refused')}"
                ),
            }
        if key == AIProvider.GEMINI.value:
            api_key = self._provider_overrides.get("gemini", {}).get("api_key") or settings.gemini_api_key
            if not api_key:
                return {"provider": "gemini", "ok": False, "local": False, "message": "Gemini API key not configured"}
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    res = await client.get(
                        "https://generativelanguage.googleapis.com/v1beta/models",
                        params={"key": api_key},
                    )
                    ok = res.status_code == 200
                    return {
                        "provider": "gemini",
                        "ok": ok,
                        "local": False,
                        "message": "Gemini API connection verified" if ok else f"Gemini HTTP {res.status_code}",
                    }
            except Exception as exc:
                return {"provider": "gemini", "ok": False, "local": False, "message": str(exc)}
        if key == AIProvider.OPENAI.value:
            override = self._provider_overrides.get("openai", {})
            api_key = override.get("api_key") or settings.openai_api_key
            base_url = override.get("base_url", settings.openai_base_url).rstrip("/")
            if not api_key:
                return {"provider": "openai", "ok": False, "local": False, "message": "OpenAI API key not configured"}
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    res = await client.get(f"{base_url}/models", headers={"Authorization": f"Bearer {api_key}"})
                    ok = res.status_code == 200
                    return {
                        "provider": "openai",
                        "ok": ok,
                        "local": False,
                        "message": "OpenAI-compatible API verified" if ok else f"HTTP {res.status_code}",
                    }
            except Exception as exc:
                return {"provider": "openai", "ok": False, "local": False, "message": str(exc)}
        if key in self._custom_providers:
            cfg = self._custom_providers[key]
            base_url = str(cfg.get("base_url", "")).rstrip("/")
            if not base_url:
                return {"provider": key, "ok": False, "local": bool(cfg.get("local")), "message": "Missing base_url"}
            headers = {"Authorization": f"Bearer {cfg['api_key']}"} if cfg.get("api_key") else {}
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    res = await client.get(f"{base_url}/models", headers=headers)
                    ok = res.status_code == 200
                    return {
                        "provider": key,
                        "ok": ok,
                        "local": bool(cfg.get("local", False)),
                        "message": "Custom provider reachable" if ok else f"HTTP {res.status_code}",
                    }
            except Exception as exc:
                return {"provider": key, "ok": False, "local": bool(cfg.get("local")), "message": str(exc)}
        return {"provider": key, "ok": False, "local": False, "message": f"Unknown provider '{provider}'"}

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

    async def pull_ollama_model(self, model_name: str) -> dict[str, Any]:
        """Request Ollama to pull a quantized model (returns honest offline state if daemon unavailable)."""
        settings = get_settings()
        base_url = self._provider_overrides.get("ollama", {}).get(
            "base_url", settings.ollama_base_url
        ).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{base_url}/api/pull",
                    json={"name": model_name, "stream": False},
                )
                res.raise_for_status()
                return {"ok": True, "model": model_name, "status": res.json().get("status", "success")}
        except Exception as exc:
            return {"ok": False, "model": model_name, "status": "unavailable", "error": str(exc)}


_ai_router: Optional[AIRouter] = None


def get_ai_router() -> AIRouter:
    """Get or create the AIRouter singleton."""
    global _ai_router
    if _ai_router is None:
        _ai_router = AIRouter()
    return _ai_router
