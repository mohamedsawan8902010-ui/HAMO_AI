import http.client
import json
import os
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["HAMO_PROVIDER"] = "mock"

import main  # noqa: E402


class ServerCase(unittest.TestCase):
    rate_limit = 1000

    @classmethod
    def setUpClass(cls):
        cls.server = main.make_server("127.0.0.1", 0, rate_limit=cls.rate_limit)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(2)

    def call(self, method, path, body=None, headers=None, host=None, json_type=True):
        hdrs = {"Host": host or f"127.0.0.1:{self.port}"}
        data = None
        if body is not None:
            data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
            if json_type:
                hdrs["Content-Type"] = "application/json"
        hdrs.update(headers or {})
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request(method, path, body=data, headers=hdrs)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp, raw

    def chat(self, payload, **kw):
        resp, raw = self.call("POST", "/api/chat", payload, **kw)
        try:
            return resp, json.loads(raw.decode("utf-8"))
        except ValueError:
            return resp, None


class HealthAndStatic(ServerCase):
    def test_health(self):
        resp, raw = self.call("GET", "/health")
        data = json.loads(raw)
        self.assertEqual(resp.status, 200)
        self.assertEqual((data["status"], data["project"], data["version"]), ("ok", "HAMO AI", main.VERSION))
        self.assertEqual(data["provider"], "mock")

    def test_serves_frontend(self):
        resp, raw = self.call("GET", "/")
        self.assertEqual(resp.status, 200)
        self.assertIn("text/html", resp.getheader("Content-Type"))
        self.assertIn("HAMO AI", raw.decode("utf-8"))
        self.assertIn("default-src 'self'", resp.getheader("Content-Security-Policy"))
        resp, _ = self.call("GET", "/app.js")
        self.assertEqual(resp.status, 200)
        self.assertIn("javascript", resp.getheader("Content-Type"))

    def test_path_traversal_blocked(self):
        for path in ("/../backend/main.py", "/%2e%2e/backend/main.py", "/..%2fbackend/main.py",
                     "/%00", "/frontend/../../etc/passwd", "/../.env"):
            with self.subTest(path=path):
                resp, raw = self.call("GET", path)
                self.assertEqual(resp.status, 404)
                self.assertNotIn(b"import ", raw)

    def test_unknown_routes(self):
        self.assertEqual(self.call("GET", "/api/nope")[0].status, 404)
        self.assertEqual(self.call("POST", "/api/other", {"a": 1})[0].status, 404)
        resp, _ = self.call("OPTIONS", "/api/chat")
        self.assertEqual(resp.status, 405)
        self.assertIsNone(resp.getheader("Access-Control-Allow-Origin"))

    def test_no_cors_headers_anywhere(self):
        resp, _ = self.call("GET", "/health")
        self.assertIsNone(resp.getheader("Access-Control-Allow-Origin"))


class ChatApi(ServerCase):
    def test_success_and_response_shape(self):
        resp, data = self.chat({"message": "ما هو الفاعل؟"})
        self.assertEqual(resp.status, 200)
        self.assertEqual((data["status"], data["project"]), ("success", "HAMO AI"))
        self.assertIn("الفاعل", data["reply"])

    def test_backward_compatible_with_v01_payload(self):
        resp, data = self.chat({"message": "OK?"})
        self.assertEqual(resp.status, 200)
        self.assertEqual(data["status"], "success")

    def test_mode_and_history_reach_the_model(self):
        history = [{"role": "user", "text": "سؤال سابق"}, {"role": "assistant", "text": "رد سابق"}]
        resp, data = self.chat({"message": "نص الدرس", "mode": "explain", "history": history})
        self.assertEqual(resp.status, 200)
        self.assertIn("(3 في السياق)", data["reply"])       # history(2) + current turn
        self.assertIn("المطلوب: اشرح", data["reply"])        # mode directive applied
        self.assertIn("نعم", data["reply"])                  # system instruction present

    def test_validation_errors_return_400_json(self):
        bad_payloads = [[1, 2], {"message": ""}, {"message": "x", "mode": "zzz"},
                        {"message": "x", "history": [1]}, "just a string"]
        for payload in bad_payloads:
            with self.subTest(payload=str(payload)):
                resp, data = self.chat(payload)
                self.assertEqual(resp.status, 400)
                self.assertIn("error", data)

    def test_invalid_json_and_missing_body(self):
        resp, _ = self.call("POST", "/api/chat", b"{not json")
        self.assertEqual(resp.status, 400)
        resp, _ = self.call("POST", "/api/chat", b"\xff\xfe")
        self.assertEqual(resp.status, 400)
        resp, _ = self.call("POST", "/api/chat", headers={"Content-Type": "application/json", "Content-Length": "0"})
        self.assertEqual(resp.status, 400)

    def test_oversized_body_rejected(self):
        resp, _ = self.call("POST", "/api/chat", b"{" + b" " * (main.MAX_BODY_BYTES + 10) + b"}")
        self.assertEqual(resp.status, 413)

    def test_cross_site_requests_are_rejected(self):
        # Content-Type text/plain is how a hostile web page avoids a CORS preflight.
        resp, _ = self.call("POST", "/api/chat", {"message": "hi"}, json_type=False,
                            headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status, 415)
        resp, _ = self.chat({"message": "hi"}, headers={"Origin": "https://evil.example"})
        self.assertEqual(resp.status, 403)
        resp, _ = self.chat({"message": "hi"}, headers={"Origin": "null"})
        self.assertEqual(resp.status, 403)

    def test_same_origin_post_allowed(self):
        resp, _ = self.chat({"message": "hi"}, headers={"Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(resp.status, 200)

    def test_foreign_host_header_rejected_dns_rebinding(self):
        resp, _ = self.call("GET", "/health", host="evil.example")
        self.assertEqual(resp.status, 403)
        resp, _ = self.chat({"message": "hi"}, host="evil.example:8000")
        self.assertEqual(resp.status, 403)

    def test_provider_error_is_sanitized(self):
        resp, data = self.chat({"message": "[fail:429]"})
        self.assertEqual(resp.status, 429)
        self.assertIn("حد الاستخدام", data["error"])
        self.assertNotIn("mock 429", data["error"])   # internal detail never reaches the client

    def test_unexpected_exception_gives_500_json(self):
        resp, data = self.chat({"message": "[crash]"})
        self.assertEqual(resp.status, 500)
        self.assertNotIn("mock crash", data["error"])


class RateLimited(ServerCase):
    rate_limit = 2

    def test_third_request_is_limited(self):
        codes = [self.chat({"message": f"m{i}"})[0].status for i in range(3)]
        self.assertEqual(codes, [200, 200, 429])
        # invalid requests do not consume quota
        self.assertEqual(self.chat({"message": ""})[0].status, 400)


if __name__ == "__main__":
    unittest.main()
