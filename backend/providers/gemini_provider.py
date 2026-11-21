"""Google Gemini provider (generateContent REST API).

Live-tested by the project owner with model gemini-3.5-flash-lite.
Provider interface:  generate(system, turns) -> str
  system: system instruction text (may be empty)
  turns:  [{"role": "user" | "assistant", "text": "..."}], first and last are "user"
"""

import os
import re

from .base import ProviderError, load_env, post_json

DEFAULT_MODEL = "gemini-3.5-flash-lite"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
_MODEL_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _model_name():
    name = (os.getenv("GEMINI_MODEL") or DEFAULT_MODEL).strip()
    if not _MODEL_RE.match(name):
        raise ProviderError("اسم نموذج Gemini في ملف .env غير صالح.", 503,
                            f"invalid GEMINI_MODEL={name!r}")
    return name


def generate(system, turns):
    load_env()
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise ProviderError(
            "مفتاح GEMINI_API_KEY غير مُعدّ. أضِفه إلى ملف .env ثم أعد تشغيل الخادم.",
            503, "GEMINI_API_KEY is missing")

    payload = {
        "contents": [
            {
                "role": "user" if turn["role"] == "user" else "model",
                "parts": [{"text": turn["text"]}],
            }
            for turn in turns
        ]
    }
    if system:
        payload["system_instruction"] = {"parts": [{"text": system}]}

    result = post_json(
        f"{_BASE_URL}{_model_name()}:generateContent",
        payload,
        {"x-goog-api-key": api_key},
    )

    candidates = result.get("candidates") or []
    if not candidates:
        block = (result.get("promptFeedback") or {}).get("blockReason")
        raise ProviderError("رفض المزوّد الإجابة عن هذه الرسالة. جرّب صياغة أخرى.", 502,
                            f"no candidates, blockReason={block}")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "\n".join(
        part["text"] for part in parts
        if isinstance(part.get("text"), str) and not part.get("thought")
    ).strip()
    if not text:
        raise ProviderError("لم يُرجع المزوّد نصًا لهذه الرسالة. جرّب إعادة صياغتها.", 502,
                            f"empty text, finishReason={candidates[0].get('finishReason')}")
    return text


def generate_reply(message, system=None, history=None):
    """Convenience wrapper (kept for the old CLI smoke test)."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message cannot be empty")
    turns = list(history or []) + [{"role": "user", "text": message.strip()}]
    return generate(system or "", turns)
