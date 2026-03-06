import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request

app = Flask(__name__)


class TTLCache:
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        hit = self._store.get(key)
        if not hit:
            return None
        expires_at, value = hit
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self.ttl_seconds, value)


class ProviderHTTPError(Exception):
    def __init__(self, provider: str, status: Optional[int], message: str):
        super().__init__(message)
        self.provider = provider
        self.status = status


class BaseProvider:
    name = "base"

    def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_chart(self, ticker: str, interval: str = "1d", range_value: str = "1mo") -> Dict[str, Any]:
        raise NotImplementedError

    def get_company(self, ticker: str) -> Dict[str, Any]:
        raise NotImplementedError


class YahooProvider(BaseProvider):
    name = "yahoo"
    base_url = "https://query1.finance.yahoo.com"

    def _request(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query = urlencode(params)
        url = f"{self.base_url}{path}?{query}"
        req = Request(url, headers={"User-Agent": "iGaruda-Terminal/1.0"})
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderHTTPError(self.name, exc.code, f"{self.name} HTTP {exc.code}") from exc
        except URLError as exc:
            raise ProviderHTTPError(self.name, None, f"{self.name} network error: {exc}") from exc

    def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        raw = self._request("/v7/finance/quote", {"symbols": ",".join(symbols)})
        results = raw.get("quoteResponse", {}).get("result", [])
        return [normalize_quote(item, self.name) for item in results]

    def get_chart(self, ticker: str, interval: str = "1d", range_value: str = "1mo") -> Dict[str, Any]:
        raw = self._request(f"/v8/finance/chart/{ticker}", {"interval": interval, "range": range_value})
        result = raw.get("chart", {}).get("result", [{}])[0]
        return {
            "symbol": ticker.upper(),
            "timestamps": result.get("timestamp", []),
            "close": result.get("indicators", {}).get("quote", [{}])[0].get("close", []),
            "source": self.name,
        }

    def get_company(self, ticker: str) -> Dict[str, Any]:
        raw = self._request(f"/v10/finance/quoteSummary/{ticker}", {"modules": "price,assetProfile"})
        result = raw.get("quoteSummary", {}).get("result", [{}])[0]
        profile = result.get("assetProfile", {})
        price = result.get("price", {})
        return {
            "symbol": ticker.upper(),
            "name": price.get("longName") or price.get("shortName") or ticker.upper(),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "website": profile.get("website"),
            "description": profile.get("longBusinessSummary"),
            "source": self.name,
        }


class ProviderBackup1(YahooProvider):
    name = "yahoo-backup-1"


class ProviderBackup2(YahooProvider):
    name = "yahoo-backup-2"


def normalize_quote(item: Dict[str, Any], source: str) -> Dict[str, Any]:
    as_of = item.get("regularMarketTime")
    if isinstance(as_of, (int, float)):
        as_of = datetime.fromtimestamp(as_of, tz=timezone.utc).isoformat()
    return {
        "symbol": item.get("symbol"),
        "price": item.get("regularMarketPrice"),
        "changePercent": item.get("regularMarketChangePercent"),
        "volume": item.get("regularMarketVolume"),
        "asOf": as_of,
        "source": source,
    }


FALLBACK_STATUSES = {401, 403, 429}
providers: List[BaseProvider] = [YahooProvider(), ProviderBackup1(), ProviderBackup2()]
quotes_cache = TTLCache(ttl_seconds=int(os.getenv("QUOTES_CACHE_TTL", "20")))
chart_cache = TTLCache(ttl_seconds=int(os.getenv("CHART_CACHE_TTL", "30")))
company_cache = TTLCache(ttl_seconds=int(os.getenv("COMPANY_CACHE_TTL", "180")))


def run_provider_chain(operation: str, cache: TTLCache, cache_key: str, *args, **kwargs) -> Tuple[Any, Dict[str, Any]]:
    cached = cache.get(cache_key)
    if cached is not None:
        payload, meta = cached
        return payload, {**meta, "cached": True}

    errors: List[Dict[str, Any]] = []
    for index, provider in enumerate(providers):
        method = getattr(provider, operation)
        try:
            payload = method(*args, **kwargs)
            metadata = {
                "provider": provider.name,
                "fallbackUsed": index > 0,
                "errors": errors,
                "cached": False,
            }
            cache.set(cache_key, (payload, metadata))
            return payload, metadata
        except ProviderHTTPError as exc:
            errors.append({"provider": provider.name, "status": exc.status, "message": str(exc)})
            if exc.status not in FALLBACK_STATUSES or index == len(providers) - 1:
                break
        except Exception as exc:
            errors.append({"provider": provider.name, "status": None, "message": str(exc)})
            break

    return None, {"provider": None, "fallbackUsed": True, "errors": errors, "cached": False}


@app.get("/api/quotes")
def api_quotes():
    symbols = request.args.get("symbols", "AAPL,MSFT,GOOG")
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    payload, metadata = run_provider_chain("get_quotes", quotes_cache, f"quotes:{','.join(symbol_list)}", symbol_list)
    if payload is None:
        return jsonify({"data": [], "meta": metadata}), 502
    return jsonify({"data": payload, "meta": metadata})


@app.get("/api/chart/<ticker>")
def api_chart(ticker: str):
    interval = request.args.get("interval", "1d")
    range_value = request.args.get("range", "1mo")
    cache_key = f"chart:{ticker.upper()}:{interval}:{range_value}"
    payload, metadata = run_provider_chain("get_chart", chart_cache, cache_key, ticker, interval=interval, range_value=range_value)
    if payload is None:
        return jsonify({"data": None, "meta": metadata}), 502
    return jsonify({"data": payload, "meta": metadata})


@app.get("/api/company/<ticker>")
def api_company(ticker: str):
    cache_key = f"company:{ticker.upper()}"
    payload, metadata = run_provider_chain("get_company", company_cache, cache_key, ticker)
    if payload is None:
        return jsonify({"data": None, "meta": metadata}), 502
    return jsonify({"data": payload, "meta": metadata})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
