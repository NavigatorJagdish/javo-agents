"""Hindi & Hinglish Hook Writer skill for short-form creator retention."""

from __future__ import annotations

from typing import Any

HINGLISH_TEMPLATES = [
    ("curiosity", "99% log {topic} mein yeh galti karte hain — aap mat karna!"),
    ("contrarian", "Agar aapko lagta hai {topic} mushkil hai, toh yeh 30 second ka trick dekho."),
    ("outcome", "Sirf 7 din mein {topic} se result kaise laayein — step by step."),
    ("secret", "{topic} ka woh hidden rule jo bade creators kabhi share nahi karte."),
    ("question", "Kya aap bhi {topic} try karke thak chuke ho? Yeh ek change sab badal dega."),
]

HINDI_TEMPLATES = [
    ("curiosity", "99% लोग {topic} में यह बड़ी गलती करते हैं — आज ही सुधारें!"),
    ("contrarian", "अगर आपको लगता है {topic} बहुत कठिन है, तो यह 30 सेकंड की ट्रिक ज़रूर देखें।"),
    ("outcome", "सिर्फ 7 दिनों में {topic} से बेहतर रिज़ल्ट कैसे पाएं — आसान तरीका।"),
    ("secret", "{topic} का वह राज़ जो ज़्यादातर क्रिएटर्स आपको नहीं बताते।"),
    ("question", "क्या आप भी {topic} में अटक गए हैं? यह एक बदलाव गेम पलट सकता है।"),
]


def _estimate_retention_score(hook: str, tone: str) -> int:
    score = 72
    if "?" in hook or "!" in hook or "।" in hook:
        score += 8
    if any(ch.isdigit() for ch in hook):
        score += 7
    if len(hook) <= 95:
        score += 7
    if tone in {"energetic", "urgent", "friendly"}:
        score += 4
    return min(99, score)


def run(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate ranked Hindi/Hinglish hooks for a given creator topic."""
    topic = str(payload.get("topic", "")).strip()
    if not topic:
        raise ValueError("topic must be a non-empty string")

    language = str(payload.get("language", "hinglish")).lower().strip()
    niche = str(payload.get("niche", "creator")).strip()
    tone = str(payload.get("tone", "energetic")).lower().strip()
    count = max(1, min(10, int(payload.get("count", 5))))

    if language == "hindi":
        pool = HINDI_TEMPLATES
    elif language == "bilingual":
        pool = HINGLISH_TEMPLATES[:3] + HINDI_TEMPLATES[:2]
    else:
        language = "hinglish"
        pool = HINGLISH_TEMPLATES

    hooks = []
    for idx, (pattern, template) in enumerate(pool[:count], start=1):
        text = template.format(topic=topic)
        hooks.append(
            {
                "rank": idx,
                "pattern": pattern,
                "text": text,
                "estimated_3s_hold_score": _estimate_retention_score(text, tone),
            }
        )

    hooks.sort(key=lambda h: h["estimated_3s_hold_score"], reverse=True)
    return {
        "topic": topic,
        "niche": niche,
        "language": language,
        "tone": tone,
        "hooks": hooks,
    }
