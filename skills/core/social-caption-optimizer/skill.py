"""Social Caption Optimizer skill — deterministic, local, zero-network."""

from __future__ import annotations

import re
from typing import Any

PLATFORM_LIMITS: dict[str, dict[str, int]] = {
    "instagram": {"max_chars": 2200, "ideal_chars": 300, "max_hashtags": 15},
    "youtube": {"max_chars": 5000, "ideal_chars": 450, "max_hashtags": 8},
    "facebook": {"max_chars": 63206, "ideal_chars": 250, "max_hashtags": 5},
    "twitter": {"max_chars": 280, "ideal_chars": 220, "max_hashtags": 3},
    "linkedin": {"max_chars": 3000, "ideal_chars": 600, "max_hashtags": 5},
    "threads": {"max_chars": 500, "ideal_chars": 280, "max_hashtags": 3},
}

DEFAULT_CTA_BY_PLATFORM: dict[str, str] = {
    "instagram": "Save this for later & share with a friend who needs it!",
    "youtube": "Subscribe for daily creator tips — drop your question below.",
    "facebook": "Comment your thoughts below and follow the page for more!",
    "twitter": "Bookmark & repost if this helped.",
    "linkedin": "What has worked best for your team? Let's discuss in the comments.",
    "threads": "Follow for more daily breakdowns.",
}


def _normalize_hashtag(tag: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\u0900-\u097F]", "", tag.lstrip("#").strip())
    return f"#{cleaned}" if cleaned else ""


def run(payload: dict[str, Any]) -> dict[str, Any]:
    """Optimize caption structure, CTA, and hashtags for the target platform."""
    raw_caption = str(payload.get("draft_caption", "")).strip()
    if not raw_caption:
        raise ValueError("draft_caption must be a non-empty string")

    platform = str(payload.get("platform", "instagram")).lower().strip()
    limits = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["instagram"])

    # Collapse excessive blank lines while preserving intentional paragraph breaks
    lines = [line.strip() for line in raw_caption.splitlines()]
    cleaned_body = "\n".join(line for line in lines if line)

    # Deduplicate and cap hashtags
    raw_tags = payload.get("hashtags") or []
    inline_tags = re.findall(r"#([a-zA-Z0-9_\u0900-\u097F]+)", cleaned_body)
    seen: set[str] = set()
    final_tags: list[str] = []
    max_tags = int(payload.get("max_hashtags") or limits["max_hashtags"])

    for candidate in [*raw_tags, *inline_tags]:
        norm = _normalize_hashtag(str(candidate))
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            final_tags.append(norm)
            if len(final_tags) >= max_tags:
                break

    # Strip inline hashtag block from body if we are appending a clean block
    body_without_trailing_tags = re.sub(r"(\s*#[a-zA-Z0-9_\u0900-\u097F]+)+\s*$", "", cleaned_body).strip()
    if not body_without_trailing_tags:
        body_without_trailing_tags = cleaned_body

    cta = str(payload.get("cta") or DEFAULT_CTA_BY_PLATFORM.get(platform, "")).strip()
    parts = [body_without_trailing_tags]
    if cta and cta.lower() not in body_without_trailing_tags.lower():
        parts.append(cta)
    if final_tags:
        parts.append(" ".join(final_tags))

    optimized = "\n\n".join(parts)
    max_chars = limits["max_chars"]

    # Truncate body safely if exceeding platform hard limit
    if len(optimized) > max_chars:
        overflow = len(optimized) - max_chars + 3
        trimmed_body = body_without_trailing_tags[:-overflow].rstrip() + "..."
        rebuilt = [trimmed_body]
        if cta and len(trimmed_body) + len(cta) + 2 <= max_chars:
            rebuilt.append(cta)
        if final_tags and len("\n\n".join(rebuilt)) + len(" ".join(final_tags)) + 2 <= max_chars:
            rebuilt.append(" ".join(final_tags))
        optimized = "\n\n".join(rebuilt)[:max_chars]

    char_count = len(optimized)
    within_limit = char_count <= max_chars

    score = 60
    if within_limit:
        score += 15
    if cta:
        score += 10
    if 1 <= len(final_tags) <= limits["max_hashtags"]:
        score += 10
    if char_count <= limits["ideal_chars"] * 2:
        score += 5

    return {
        "platform": platform,
        "optimized_caption": optimized,
        "hashtags": final_tags,
        "character_count": char_count,
        "character_limit": max_chars,
        "within_limit": within_limit,
        "score": min(100, score),
    }
