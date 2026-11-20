
import json
import os
import urllib.request
import urllib.error


API_URL = "https://api.openai.com/v1/responses"

MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-6.2-astra"
)


def generate_reply(message):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message cannot be empty")

    payload = {
        "model": MODEL,
        "input": message.strip()
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI API error ({error.code}): {error_body}"
        ) from None

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Network error: {error.reason}"
        ) from None

    output_text = []

    for item in result.get("output", []):
        if item.get("type") != "message":
            continue

        for content in item.get("content", []):
            if content.get("type") == "output_text":
                output_text.append(content.get("text", ""))

    reply = "\n".join(output_text).strip()

    if not reply:
        raise RuntimeError("The model returned no text")

    return reply

