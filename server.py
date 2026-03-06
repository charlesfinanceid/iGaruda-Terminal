import os
import threading
import time
from typing import Any

import requests
from flask import Flask, jsonify, send_from_directory

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
UPSTREAM_TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT", "5"))
QUOTE_REFRESH_MS = int(os.getenv("QUOTE_REFRESH_MS", "30000"))
QUOTE_PROVIDER_URL = os.getenv("QUOTE_PROVIDER_URL", "https://api.quotable.io/random")

app = Flask(__name__, static_folder="static", static_url_path="")

_quote_lock = threading.Lock()
_cached_quote: dict[str, Any] | None = None
_last_quote_fetch_ms = 0


def now_ms() -> int:
    return int(time.time() * 1000)


def fetch_json(url: str) -> dict[str, Any]:
    """Fetch JSON from upstream with timeout protection."""
    response = requests.get(url, timeout=UPSTREAM_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Upstream JSON payload must be an object")
    return payload


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/api/quote")
def quote():
    global _cached_quote, _last_quote_fetch_ms

    now = now_ms()
    with _quote_lock:
        if _cached_quote and (now - _last_quote_fetch_ms) < QUOTE_REFRESH_MS:
            age_ms = now - _last_quote_fetch_ms
            return jsonify({"source": "cache", "age_ms": age_ms, "data": _cached_quote}), 200

        try:
            fresh_quote = fetch_json(QUOTE_PROVIDER_URL)
            _cached_quote = fresh_quote
            _last_quote_fetch_ms = now
            return jsonify({"source": "upstream", "age_ms": 0, "data": fresh_quote}), 200
        except Exception as exc:  # fallback keeps UI alive when upstream is flaky
            if _cached_quote:
                age_ms = now - _last_quote_fetch_ms
                return (
                    jsonify(
                        {
                            "source": "stale-cache",
                            "age_ms": age_ms,
                            "warning": str(exc),
                            "data": _cached_quote,
                        }
                    ),
                    200,
                )
            return jsonify({"error": "Unable to fetch quote", "detail": str(exc)}), 502


@app.get("/")
def root():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
