import json
import os
import random
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
UPSTREAM_TIMEOUT = int(os.getenv("UPSTREAM_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))
QUOTE_REFRESH_MS = int(os.getenv("QUOTE_REFRESH_MS", "30000"))

QUOTES = [
    "Great things are done by a series of small things brought together.",
    "Simplicity is the soul of efficiency.",
    "First, solve the problem. Then, write the code.",
    "Quality means doing it right when no one is looking.",
]


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/health":
            self._send_json({"status": "ok"}, status=200)
            return

        if path == "/api/quotes":
            self._send_json(
                {
                    "quote": random.choice(QUOTES),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "config": {
                        "upstream_timeout": UPSTREAM_TIMEOUT,
                        "cache_ttl_seconds": CACHE_TTL_SECONDS,
                        "quote_refresh_ms": QUOTE_REFRESH_MS,
                    },
                },
                status=200,
            )
            return

        if path == "/":
            self._send_html(
                """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>iGaruda Terminal</title>
</head>
<body>
  <main>
    <h1>iGaruda Terminal</h1>
    <p>App is online.</p>
    <p>Try <code>/health</code> and <code>/api/quotes</code>.</p>
  </main>
</body>
</html>
""".strip()
            )
            return

        self._send_json({"error": "not found"}, status=404)


if __name__ == "__main__":
    print(f"Starting server on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), AppHandler).serve_forever()
