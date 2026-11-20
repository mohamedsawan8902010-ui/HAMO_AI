
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from providers.gemini_provider import generate_reply

HOST = "127.0.0.1"
PORT = 8000
MAX_MESSAGE_SIZE = 16_384


class HAMOAIHandler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, status, data):
        response = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_cors_headers()
        self.send_header(
            "Content-Length",
            str(len(response))
        )
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "status": "ok",
                "project": "HAMO AI",
                "version": "0.1.0"
            })
        else:
            self.send_json(404, {
                "error": "Endpoint not found"
            })

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_json(404, {
                "error": "Endpoint not found"
            })
            return

        try:
            length = int(
                self.headers.get("Content-Length", "0")
            )

            if length <= 0 or length > MAX_MESSAGE_SIZE:
                self.send_json(400, {
                    "error": "Invalid message size"
                })
                return

            data = json.loads(
                self.rfile.read(length).decode("utf-8")
            )

            message = data.get("message")

            if not isinstance(message, str) or not message.strip():
                self.send_json(400, {
                    "error": "Message is required"
                })
                return

            reply = generate_reply(message)

            self.send_json(200, {
                "status": "success",
                "project": "HAMO AI",
                "reply": reply
            })

        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {
                "error": "Invalid request"
            })

        except RuntimeError as error:
            self.send_json(502, {
                "error": str(error)
            })

    def log_message(self, format, *args):
        print("[HAMO AI]", format % args)


def main():
    server = ThreadingHTTPServer(
        (HOST, PORT),
        HAMOAIHandler
    )

    print("=" * 35)
    print("       HAMO AI SERVER")
    print("=" * 35)
    print(f"Server running at http://{HOST}:{PORT}")
    print("Version: 0.1.0")
    print("Press CTRL+C to stop.")
    print("=" * 35)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping HAMO AI...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

