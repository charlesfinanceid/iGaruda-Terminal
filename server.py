import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if self.path == "/":
            self._send_json(
                200,
                {
                    "message": "Backend service is running.",
                    "health": "/health",
                },
            )
            return

        self._send_json(404, {"error": "Not found"})


def run_server():
    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0"
    server = HTTPServer((host, port), AppHandler)
    print(f"Server listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
