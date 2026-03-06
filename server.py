import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)


class ProviderError(Exception):
    pass


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_chart(self, symbol: str, interval: str, range_: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_company(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError


class YahooProvider(MarketDataProvider):
    name = "yahoo"
    base_url = "https://query1.finance.yahoo.com"

    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        if not symbols:
            raise ProviderError("symbols is required")

        resp = requests.get(
            f"{self.base_url}/v7/finance/quote",
            params={"symbols": ",".join(symbols)},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        results = payload.get("quoteResponse", {}).get("result", [])
        if not results:
            raise ProviderError("no quote results")

        output = {}
        for row in results:
            symbol = row.get("symbol")
            price = row.get("regularMarketPrice")
            if symbol and price is not None:
                output[symbol] = {
                    "symbol": symbol,
                    "price": price,
                    "currency": row.get("currency"),
                    "change": row.get("regularMarketChange"),
                    "changePercent": row.get("regularMarketChangePercent"),
                }

        if not output:
            raise ProviderError("quotes missing valid prices")
        return {"quotes": output}

    def get_chart(self, symbol: str, interval: str, range_: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/v8/finance/chart/{symbol}",
            params={"interval": interval, "range": range_},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        result = payload.get("chart", {}).get("result") or []
        if not result:
            raise ProviderError("chart not found")

        row = result[0]
        timestamps = row.get("timestamp") or []
        indicators = row.get("indicators", {}).get("quote", [{}])
        closes = indicators[0].get("close") if indicators else []

        points = [
            {"timestamp": ts, "close": close}
            for ts, close in zip(timestamps, closes)
            if close is not None
        ]
        if not points:
            raise ProviderError("chart contains no valid points")

        return {"symbol": symbol.upper(), "interval": interval, "range": range_, "points": points}

    def get_company(self, symbol: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/v10/finance/quoteSummary/{symbol}",
            params={"modules": "price,assetProfile"},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        result = payload.get("quoteSummary", {}).get("result") or []
        if not result:
            raise ProviderError("company profile not found")

        row = result[0]
        price = row.get("price", {})
        profile = row.get("assetProfile", {})
        return {
            "symbol": symbol.upper(),
            "name": price.get("longName") or price.get("shortName"),
            "exchange": price.get("exchangeName"),
            "industry": profile.get("industry"),
            "sector": profile.get("sector"),
            "website": profile.get("website"),
            "description": profile.get("longBusinessSummary"),
        }


class AlphaVantageProvider(MarketDataProvider):
    name = "alphavantage"
    base_url = "https://www.alphavantage.co/query"

    def __init__(self) -> None:
        self.api_key = os.getenv("ALPHAVANTAGE_API_KEY")

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderError("ALPHAVANTAGE_API_KEY not set")

        resp = requests.get(self.base_url, params={**params, "apikey": self.api_key}, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("Note"):
            raise ProviderError(payload["Note"])
        if payload.get("Error Message"):
            raise ProviderError(payload["Error Message"])
        return payload

    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        if not symbols:
            raise ProviderError("symbols is required")

        output = {}
        for symbol in symbols:
            payload = self._request({"function": "GLOBAL_QUOTE", "symbol": symbol})
            quote = payload.get("Global Quote") or {}
            price_raw = quote.get("05. price")
            if not price_raw:
                continue
            output[symbol.upper()] = {
                "symbol": symbol.upper(),
                "price": float(price_raw),
                "change": float(quote.get("09. change", 0) or 0),
                "changePercent": quote.get("10. change percent"),
            }

        if not output:
            raise ProviderError("no quote results")
        return {"quotes": output}

    def get_chart(self, symbol: str, interval: str, range_: str) -> Dict[str, Any]:
        # Alpha Vantage free endpoint offers daily bars without intraday history guarantees.
        payload = self._request({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact"})
        series = payload.get("Time Series (Daily)") or {}
        if not series:
            raise ProviderError("chart data not found")

        points = []
        for date_str, values in series.items():
            close_val = values.get("4. close")
            if close_val is None:
                continue
            points.append({"date": date_str, "close": float(close_val)})

        if not points:
            raise ProviderError("chart contains no valid points")

        points = sorted(points, key=lambda x: x["date"])
        return {"symbol": symbol.upper(), "interval": interval, "range": range_, "points": points}

    def get_company(self, symbol: str) -> Dict[str, Any]:
        payload = self._request({"function": "OVERVIEW", "symbol": symbol})
        if not payload or not payload.get("Symbol"):
            raise ProviderError("company profile not found")

        return {
            "symbol": payload.get("Symbol"),
            "name": payload.get("Name"),
            "exchange": payload.get("Exchange"),
            "industry": payload.get("Industry"),
            "sector": payload.get("Sector"),
            "website": payload.get("Website"),
            "description": payload.get("Description"),
        }


PROVIDERS: List[MarketDataProvider] = [YahooProvider(), AlphaVantageProvider()]


def call_with_fallback(fetcher: Callable[[MarketDataProvider], Dict[str, Any]]):
    errors = []
    for idx, provider in enumerate(PROVIDERS):
        try:
            data = fetcher(provider)
            data["provider"] = provider.name
            data["fallbackUsed"] = idx > 0
            data["errors"] = errors
            return data, 200
        except Exception as exc:
            errors.append({"provider": provider.name, "error": str(exc)})

    return {
        "error": "All providers failed",
        "provider": None,
        "fallbackUsed": False,
        "errors": errors,
    }, 502


@app.get("/api/quotes")
def api_quotes():
    raw_symbols = request.args.get("symbols", "")
    symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
    if not symbols:
        return jsonify({"error": "symbols query param is required"}), 400

    body, status = call_with_fallback(lambda provider: provider.get_quotes(symbols))
    return jsonify(body), status


@app.get("/api/chart")
def api_chart():
    symbol = (request.args.get("symbol") or "").strip().upper()
    interval = (request.args.get("interval") or "1d").strip()
    range_ = (request.args.get("range") or "1mo").strip()

    if not symbol:
        return jsonify({"error": "symbol query param is required"}), 400

    body, status = call_with_fallback(
        lambda provider: provider.get_chart(symbol=symbol, interval=interval, range_=range_)
    )
    return jsonify(body), status


@app.get("/api/company")
def api_company():
    symbol = (request.args.get("symbol") or "").strip().upper()
    if not symbol:
        return jsonify({"error": "symbol query param is required"}), 400

    body, status = call_with_fallback(lambda provider: provider.get_company(symbol))
    return jsonify(body), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
