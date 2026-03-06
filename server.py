from __future__ import annotations

import random
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)

QUOTE_TTL_SECONDS = 5
CHART_TTL_SECONDS = 60


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class EndpointSymbolCache:
    """Simple in-memory cache keyed by (endpoint, symbol) with per-endpoint TTL."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], CacheEntry] = {}
        self._lock = Lock()

    def get(self, endpoint: str, symbol: str) -> Any | None:
        now = time.time()
        key = (endpoint, symbol)
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if entry.expires_at <= now:
                self._store.pop(key, None)
                return None
            return entry.value

    def set(self, endpoint: str, symbol: str, value: Any, ttl_seconds: int) -> Any:
        key = (endpoint, symbol)
        with self._lock:
            self._store[key] = CacheEntry(value=value, expires_at=time.time() + ttl_seconds)
        return value


cache = EndpointSymbolCache()


def fetch_quote_from_source(symbol: str) -> dict[str, Any]:
    # TODO: replace with real market data provider integration.
    base = 100 + (hash(symbol) % 300)
    drift = random.uniform(-3, 3)
    price = round(base + drift, 2)
    return {
        "symbol": symbol,
        "price": price,
        "source": "live",
        "timestamp": int(time.time()),
    }


def fetch_chart_from_source(symbol: str) -> dict[str, Any]:
    now = int(time.time())
    points = []
    anchor = 100 + (hash(symbol) % 300)
    for idx in range(30):
        points.append(
            {
                "t": now - (29 - idx) * 60,
                "v": round(anchor + random.uniform(-8, 8), 2),
            }
        )

    return {
        "symbol": symbol,
        "interval": "1m",
        "points": points,
        "source": "live",
        "timestamp": now,
    }


def normalize_symbol(raw: str | None) -> str:
    return (raw or "").strip().upper()


@app.get("/api/quote")
def get_quote():
    symbol = normalize_symbol(request.args.get("symbol"))
    if not symbol:
        return jsonify({"error": "symbol is required"}), 400

    cached = cache.get("quote", symbol)
    if cached is not None:
        result = dict(cached)
        result["cache"] = "hit"
        return jsonify(result)

    fresh = fetch_quote_from_source(symbol)
    cache.set("quote", symbol, fresh, QUOTE_TTL_SECONDS)

    result = dict(fresh)
    result["cache"] = "miss"
    return jsonify(result)


@app.get("/api/chart")
def get_chart():
    symbol = normalize_symbol(request.args.get("symbol"))
    if not symbol:
        return jsonify({"error": "symbol is required"}), 400

    cached = cache.get("chart", symbol)
    if cached is not None:
        result = dict(cached)
        result["cache"] = "hit"
        return jsonify(result)

    fresh = fetch_chart_from_source(symbol)
    cache.set("chart", symbol, fresh, CHART_TTL_SECONDS)

    result = dict(fresh)
    result["cache"] = "miss"
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
