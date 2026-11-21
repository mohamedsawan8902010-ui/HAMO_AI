"""OpenAI provider (Responses API) -- EXPERIMENTAL, NOT TESTED.

Needs OPENAI_API_KEY and OPENAI_MODEL in .env. There is deliberately no default
model: model names change, so set one you have verified in your OpenAI account.
Enable with HAMO_PROVIDER=openai.
"""

import os

from .base import ProviderError, load_env, post_json

API_URL = "https://api.openai.com/v1/responses"


def generate(system, turns):
    load_env()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    model = (os.getenv("OPENAI_MODEL") or "").strip()
    if not api_key or not model:
        raise ProviderError(
            "إعدادات OpenAI ناقصة. أضِف OPENAI_API_KEY و OPENAI_MODEL إلى ملف .env.",
            503, "OPENAI_API_KEY or OPENAI_MODEL is missing")

    payload = {
        "model": model,
        "input": [{"role": t["role"], "content": t["text"]} for t in turns],
    }
    if system:
        payload["instructions"] = system

    result = post_json(API_URL, payload, {"Authorization": f"Bearer {api_key}"})

    chunks = []
    for item in result.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    text = "\n".join(chunks).strip()
    if not text:
        raise ProviderError("لم يُرجع المزوّد نصًا لهذه الرسالة.", 502, "empty OpenAI output")
    return text
