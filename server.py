import json
import logging
import os
import threading
import time
import uuid
from collections import defaultdict
from typing import Dict

from flask import Flask, g, jsonify, request


class JsonFormatter(logging.Formatter):
    """Render log records as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Include known structured fields when present.
        for field in (
            "request_id",
            "endpoint",
            "provider",
            "status_code",
            "latency_ms",
            "error_class",
            "error_message",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("backend")
    logger.setLevel(level)
    logger.propagate = False

    # Replace handlers so formatter stays deterministic.
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger


LOGGER = configure_logging()


class MetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.success_by_provider: Dict[str, int] = defaultdict(int)
        self.fail_by_provider: Dict[str, int] = defaultdict(int)
        self.cache_hits = 0
        self.cache_lookups = 0
        self.fallback_usage = 0

    def record_provider_result(self, provider: str, success: bool) -> None:
        with self._lock:
            if success:
                self.success_by_provider[provider] += 1
            else:
                self.fail_by_provider[provider] += 1

    def record_cache(self, hit: bool) -> None:
        with self._lock:
            self.cache_lookups += 1
            if hit:
                self.cache_hits += 1

    def record_fallback(self) -> None:
        with self._lock:
            self.fallback_usage += 1

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            hit_ratio = (
                self.cache_hits / self.cache_lookups if self.cache_lookups > 0 else 0.0
            )
            return {
                "success_by_provider": dict(self.success_by_provider),
                "fail_by_provider": dict(self.fail_by_provider),
                "cache": {
                    "hits": self.cache_hits,
                    "lookups": self.cache_lookups,
                    "hit_ratio": round(hit_ratio, 4),
                },
                "fallback_usage": self.fallback_usage,
            }


METRICS = MetricsStore()
app = Flask(__name__)


def _request_id() -> str:
    header_value = request.headers.get("X-Request-ID", "").strip()
    return header_value or str(uuid.uuid4())


@app.before_request
def before_request() -> None:
    g.request_started = time.perf_counter()
    g.request_id = _request_id()
    g.provider = request.headers.get("X-Provider", "unknown")
    g.error_class = None
    g.error_message = None


@app.after_request
def after_request(response):
    latency_ms = round((time.perf_counter() - g.request_started) * 1000, 2)

    LOGGER.info(
        "request_completed",
        extra={
            "request_id": g.request_id,
            "endpoint": request.path,
            "provider": g.provider,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "error_class": g.error_class,
            "error_message": g.error_message,
        },
    )
    response.headers["X-Request-ID"] = g.request_id
    return response


@app.errorhandler(Exception)
def handle_exception(error: Exception):
    g.error_class = error.__class__.__name__
    g.error_message = str(error)
    provider = getattr(g, "provider", "unknown")
    METRICS.record_provider_result(provider, success=False)

    return jsonify({"error": "internal_server_error", "request_id": g.request_id}), 500


@app.get("/health")
def healthcheck():
    return jsonify({"status": "ok"})


@app.get("/generate")
def generate():
    """Example endpoint to demonstrate provider/caching/fallback metrics."""
    provider = request.args.get("provider", "primary")
    cache_hit = request.args.get("cache_hit", "false").lower() == "true"
    use_fallback = request.args.get("fallback", "false").lower() == "true"
    force_error = request.args.get("force_error", "false").lower() == "true"

    g.provider = provider
    METRICS.record_cache(cache_hit)

    if use_fallback:
        METRICS.record_fallback()

    if force_error:
        METRICS.record_provider_result(provider, success=False)
        raise RuntimeError("forced provider failure")

    METRICS.record_provider_result(provider, success=True)
    return jsonify(
        {
            "result": "ok",
            "provider": provider,
            "cache_hit": cache_hit,
            "fallback": use_fallback,
            "request_id": g.request_id,
        }
    )


@app.get("/metrics")
def metrics():
    return jsonify(METRICS.snapshot())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
