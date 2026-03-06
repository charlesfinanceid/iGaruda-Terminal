import json
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import URLError, HTTPError

from flask import Flask, Response, g, jsonify, request as flask_request

app = Flask(__name__)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("igaruda-terminal")

UPSTREAM_HEALTH_URL = os.getenv("UPSTREAM_HEALTH_URL")
UPSTREAM_TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT", "2.0"))


@app.before_request
def mark_request_start() -> None:
    g.request_start = time.perf_counter()


@app.after_request
def log_api_failures(response: Response) -> Response:
    if response.status_code >= 400:
        start = getattr(g, "request_start", None)
        latency_ms = None
        if start is not None:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)

        payload: Dict[str, Any] = {
            "event": "api_failure",
            "path": flask_request.path,
            "provider": _extract_provider(),
            "status": response.status_code,
            "latency_ms": latency_ms,
        }
        logger.error(json.dumps(payload, ensure_ascii=False))

    return response


@app.get("/health")
def health() -> Response:
    return jsonify(
        {
            "status": "ok",
            "service": "iGaruda-Terminal",
        }
    )


@app.get("/ready")
def ready() -> Response:
    upstream = _check_upstream_dependency()

    if not upstream["ok"]:
        return jsonify(
            {
                "status": "degraded",
                "service": "iGaruda-Terminal",
                "upstream": upstream,
            }
        ), 503

    return jsonify(
        {
            "status": "ready",
            "service": "iGaruda-Terminal",
            "upstream": upstream,
        }
    )


@app.errorhandler(Exception)
def handle_unexpected_error(exc: Exception):
    start = getattr(g, "request_start", None)
    latency_ms = None
    if start is not None:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

    payload = {
        "event": "api_exception",
        "path": flask_request.path,
        "provider": _extract_provider(),
        "status": 500,
        "latency_ms": latency_ms,
        "error": str(exc),
    }
    logger.exception(json.dumps(payload, ensure_ascii=False))
    return jsonify({"error": "internal_server_error"}), 500


def _extract_provider() -> Optional[str]:
    provider = flask_request.args.get("provider")
    if provider:
        return provider

    parts = [part for part in flask_request.path.split("/") if part]
    if "provider" in parts:
        idx = parts.index("provider")
        if idx + 1 < len(parts):
            return parts[idx + 1]

    return None


def _check_upstream_dependency() -> Dict[str, Any]:
    if not UPSTREAM_HEALTH_URL:
        return {
            "ok": True,
            "checked": False,
            "message": "UPSTREAM_HEALTH_URL is not configured",
        }

    req = request.Request(UPSTREAM_HEALTH_URL, method="GET")
    start = time.perf_counter()

    try:
        with request.urlopen(req, timeout=UPSTREAM_TIMEOUT) as resp:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "ok": 200 <= resp.status < 400,
                "checked": True,
                "url": UPSTREAM_HEALTH_URL,
                "status": resp.status,
                "latency_ms": latency_ms,
            }
    except HTTPError as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ok": False,
            "checked": True,
            "url": UPSTREAM_HEALTH_URL,
            "status": exc.code,
            "latency_ms": latency_ms,
            "error": str(exc),
        }
    except URLError as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ok": False,
            "checked": True,
            "url": UPSTREAM_HEALTH_URL,
            "latency_ms": latency_ms,
            "error": str(exc.reason),
        }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
