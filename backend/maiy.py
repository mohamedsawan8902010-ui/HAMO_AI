"""HAMO AI backend -- standard library only (no pip installs needed in Termux).

One server, one origin: it serves the web UI (frontend/) and the chat API, so the
browser, the Android WebView and the floating panel all use http://127.0.0.1:8000/
"""

import errno
import json
import mimetypes
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from chat import ChatError, parse_request, run_chat
from providers import ProviderError, active_provider_name

VERSION = "0.2.0"
PROJECT = "HAMO AI"
HOST = os.getenv("HAMO_HOST", "0.0.0.0")
PORT = int(os.getenv("HAMO_PORT", "8000"))
MAX_BODY_BYTES = 65_536
RATE_LIMIT_PER_MIN = int(os.getenv("HAMO_RATE_LIMIT_PER_MIN", "30"))
FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; "
       "frame-ancestors 'none'")


class RateLimiter:
    """Sliding-window limiter: protects the AI quota from loops and abuse."""

    def __init__(self, max_calls, window_seconds=60.0):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls = []
        self._lock = threading.Lock()

    def allow(self):
        now = time.monotonic()
        with self._lock:
            self._calls = [t for t in self._calls if now - t < self.window]
            if len(self._calls) >= self.max_calls:
                return False
            self._calls.append(now)
            return True


class HAMOAIHandler(BaseHTTPRequestHandler):
    server_version = "HAMOAI"
    sys_version = ""
    timeout = 30
    allowed_hosts = frozenset()
    limiter = RateLimiter(RATE_LIMIT_PER_MIN)

    # ---- helpers -------------------------------------------------------
    def _send(self, status, body, content_type, extra=None):
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "no-store",
        }
        headers.update(extra or {})
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _host_ok(self):
        # Blocks DNS-rebinding: only our own host names may talk to this server.
        return (self.headers.get("Host") or "").strip().lower() in self.allowed_hosts

    def _origin_ok(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True  # same-origin navigations and non-browser clients
        return urlsplit(origin).netloc.lower() in self.allowed_hosts

    # ---- routes --------------------------------------------------------
    def do_GET(self):
        if not self._host_ok():
            return self.send_json(403, {"error": "Host not allowed"})
        path = urlsplit(self.path).path
        if path == "/health":
            return self.send_json(200, {
                "status": "ok",
                "project": PROJECT,
                "version": VERSION,
                "provider": active_provider_name(),
            })
        if path.startswith("/api/"):
            return self.send_json(404, {"error": "Endpoint not found"})
        self._serve_static(path)

    do_HEAD = do_GET

    def _serve_static(self, url_path):
        rel = unquote(url_path)
        if rel in ("", "/"):
            rel = "/index.html"
        try:
            target = (FRONTEND_DIR / rel.lstrip("/")).resolve()
        except (OSError, ValueError):
            return self.send_json(404, {"error": "Not found"})
        if FRONTEND_DIR not in target.parents or not target.is_file():
            return self.send_json(404, {"error": "Not found"})
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/json":
            content_type += "; charset=utf-8"
        extra = {"Cache-Control": "no-cache"}
        if target.suffix == ".html":
            extra["Content-Security-Policy"] = CSP
        self._send(200, target.read_bytes(), content_type, extra)

    def do_POST(self):
        if not self._host_ok():
            return self.send_json(403, {"error": "Host not allowed"})
        if urlsplit(self.path).path != "/api/chat":
            return self.send_json(404, {"error": "Endpoint not found"})
        if not self._origin_ok():
            return self.send_json(403, {"error": "Origin not allowed"})

        content_type = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if content_type != "application/json":
            return self.send_json(415, {"error": "Content-Type must be application/json"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.send_json(400, {"error": "طلب غير صالح."})
        if length <= 0:
            return self.send_json(400, {"error": "طلب غير صالح."})
        if length > MAX_BODY_BYTES:
            return self.send_json(413, {"error": "حجم الطلب كبير جدًا."})

        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json(400, {"error": "طلب غير صالح."})

        try:
            request = parse_request(data)
            if not self.limiter.allow():
                return self.send_json(429, {
                    "error": "طلبات كثيرة خلال وقت قصير. انتظر قليلًا ثم أعد المحاولة."})
            reply = run_chat(*request)
        except ChatError as err:
            return self.send_json(400, {"error": str(err)})
        except ProviderError as err:
            print(f"[HAMO AI] provider error ({err.status}): {err.detail}", file=sys.stderr)
            return self.send_json(err.status, {"error": err.user_message})
        except Exception:
            traceback.print_exc()
            return self.send_json(500, {"error": "حدث خطأ غير متوقع في الخادم."})

        self.send_json(200, {
            "status": "success",
            "project": PROJECT,
            "reply": reply,
            "provider": active_provider_name(),
        })

    def do_OPTIONS(self):
        # No CORS on purpose: the UI is same-origin, other sites must not call the API.
        self.send_json(405, {"error": "Method not allowed"})

    def log_message(self, format, *args):
        print("[HAMO AI]", format % args)


def make_server(host=HOST, port=PORT, rate_limit=None):
    """Create the server. port=0 picks a free port (used by the tests)."""
    # Build the server first to learn the real port, then bind the handler to it.
    class _Handler(HAMOAIHandler):
        pass

    server = ThreadingHTTPServer((host, port), _Handler)
    bound = server.server_address[1]
    hosts = {f"127.0.0.1:{bound}", f"localhost:{bound}"}
    hosts |= {h.strip().lower() for h in os.getenv("HAMO_ALLOWED_HOSTS", "").split(",") if h.strip()}
    _Handler.allowed_hosts = frozenset(hosts)
    _Handler.limiter = RateLimiter(rate_limit if rate_limit is not None else RATE_LIMIT_PER_MIN)
    return server


def main():
    try:
        server = make_server()
    except OSError as err:
        if err.errno == errno.EADDRINUSE:
            print(f"ERROR: port {PORT} is already in use (an old HAMO AI server is probably running).")
            print("Stop it with CTRL+C in its Termux session, or run:  pkill -f backend/main.py")
            sys.exit(1)
        raise

    provider = active_provider_name()
    key_var = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}.get(provider)

    print("=" * 40)
    print("         HAMO AI SERVER")
    print("=" * 40)
    print(f"Open:      http://{HOST}:{PORT}/")
    print(f"Version:   {VERSION}")
    print(f"Provider:  {provider}")
    if key_var and not os.getenv(key_var):
        print(f"WARNING:   {key_var} is not set -- chat will fail until you add it to .env")
    print("Press CTRL+C to stop.")
    print("=" * 40)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping HAMO AI...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
