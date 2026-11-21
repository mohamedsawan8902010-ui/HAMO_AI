"""Shared helpers for AI providers (standard library only)."""

import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_env_loaded = False


class ProviderError(Exception):
    """Raised by providers.

    user_message is safe to show to the end user (Arabic, no secrets).
    detail is for the server log only.
    """

    def __init__(self, user_message, status=502, detail=""):
        super().__init__(user_message)
        self.user_message = user_message
        self.status = status
        self.detail = detail


def load_env(path=None):
    """Load KEY=VALUE pairs from <project>/.env (no python-dotenv needed).

    Variables that already exist in the environment always win.
    """
    global _env_loaded
    if path is None and _env_loaded:
        return
    env_path = Path(path) if path else PROJECT_ROOT / ".env"
    if env_path.is_file():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value
    if path is None:
        _env_loaded = True


def _http_error(code, body):
    detail = f"HTTP {code}: {body}"
    if code == 429:
        return ProviderError(
            "تم تجاوز حد الاستخدام لدى مزوّد الذكاء الاصطناعي مؤقتًا. حاول بعد قليل.",
            429, detail)
    if code in (401, 403):
        return ProviderError(
            "رفض المزوّد الطلب. تحقق من مفتاح API في ملف .env ومن صلاحياته.",
            502, detail)
    if code == 404:
        return ProviderError(
            "النموذج المحدد غير متاح. تحقق من اسم النموذج في ملف .env.", 502, detail)
    if code == 400:
        return ProviderError(
            "لم يقبل المزوّد الطلب. تحقق من مفتاح API ومن اسم النموذج.", 502, detail)
    if code >= 500:
        return ProviderError(
            "مزوّد الذكاء الاصطناعي غير متاح مؤقتًا. حاول بعد قليل.", 503, detail)
    return ProviderError("تعذر الحصول على رد من مزوّد الذكاء الاصطناعي.", 502, detail)


def post_json(url, payload, headers, timeout=60):
    """POST JSON and return the parsed JSON reply, or raise ProviderError."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")[:500]
        raise _http_error(err.code, body) from None
    except urllib.error.URLError as err:
        if isinstance(err.reason, (socket.timeout, TimeoutError)):
            raise ProviderError(
                "انتهت مهلة انتظار رد مزوّد الذكاء الاصطناعي. حاول مرة أخرى.",
                504, str(err.reason)) from None
        raise ProviderError(
            "تعذر الوصول إلى مزوّد الذكاء الاصطناعي. تحقق من اتصال الإنترنت في هاتفك.",
            502, str(err.reason)) from None
    except (socket.timeout, TimeoutError):
        raise ProviderError(
            "انتهت مهلة انتظار رد مزوّد الذكاء الاصطناعي. حاول مرة أخرى.",
            504, "read timeout") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ProviderError("وصل رد غير مفهوم من مزوّد الذكاء الاصطناعي.", 502,
                            "invalid JSON from provider") from None
