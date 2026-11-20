import json
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.5-flash-lite:generateContent"
)


def generate_reply(message):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message cannot be empty")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": message.strip()}
                ]
            }
        ]
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Gemini API error ({error.code}): {error_body}"
        ) from None

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Network error: {error.reason}"
        ) from None

    candidates = result.get("candidates", [])

    if not candidates:
        raise RuntimeError("Gemini returned no response")

    parts = candidates[0].get("content", {}).get("parts", [])

    reply = "\n".join(
        part.get("text", "")
        for part in parts
        if isinstance(part.get("text"), str)
    ).strip()

    if not reply:
        raise RuntimeError("Gemini returned no text")

    return reply
