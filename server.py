from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import urlopen
from typing import Any, Dict, Iterable, List, Tuple
import json

from flask import Flask, jsonify

app = Flask(__name__)

REQUEST_TIMEOUT = 10


def _http_get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    query = urlencode(params)
    full_url = f"{url}?{query}" if query else url
    with urlopen(full_url, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_get_text(url: str, params: Dict[str, Any]) -> str:
    query = urlencode(params)
    full_url = f"{url}?{query}" if query else url
    with urlopen(full_url, timeout=REQUEST_TIMEOUT) as response:
        return response.read().decode("utf-8")


class ProviderError(Exception):
    """Raised when a provider cannot serve a request."""


@dataclass
class ProviderResult:
    provider: str
    data: Any


class DataProvider(ABC):
    name: str

    @abstractmethod
    def get_quotes(self, symbols: Iterable[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_chart(self, symbol: str, interval: str, chart_range: str) -> List[Dict[str, Any]]:
        raise NotImplementedError


class YahooProvider(DataProvider):
    name = "yahoo"

    def get_quotes(self, symbols: Iterable[str]) -> List[Dict[str, Any]]:
        symbols_list = [s.strip().upper() for s in symbols if s and s.strip()]
        if not symbols_list:
            raise ProviderError("No valid symbols provided")

        payload = _http_get_json(
            "https://query1.finance.yahoo.com/v7/finance/quote",
            {"symbols": ",".join(symbols_list)},
        )

        results = payload.get("quoteResponse", {}).get("result", [])
        if not results:
            raise ProviderError("Yahoo returned no quote data")

        normalized = []
        as_of = datetime.now(timezone.utc).isoformat()
        for item in results:
            symbol = item.get("symbol")
            if not symbol:
                continue
            normalized.append(
                {
                    "symbol": symbol,
                    "price": item.get("regularMarketPrice"),
                    "changePercent": item.get("regularMarketChangePercent"),
                    "volume": item.get("regularMarketVolume"),
                    "source": self.name,
                    "asOf": as_of,
                }
            )

        if not normalized:
            raise ProviderError("Yahoo quote payload could not be normalized")
        return normalized

    def get_chart(self, symbol: str, interval: str, chart_range: str) -> List[Dict[str, Any]]:
        payload = _http_get_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            {"interval": interval, "range": chart_range},
        )
        result = payload.get("chart", {}).get("result", [])
        if not result:
            raise ProviderError("Yahoo returned no chart data")

        chart = result[0]
        timestamps = chart.get("timestamp") or []
        quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []
        volumes = quote.get("volume") or []

        points = []
        for idx, ts in enumerate(timestamps):
            close = closes[idx] if idx < len(closes) else None
            volume = volumes[idx] if idx < len(volumes) else None
            points.append(
                {
                    "time": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                    "close": close,
                    "volume": volume,
                    "source": self.name,
                }
            )

        if not points:
            raise ProviderError("Yahoo chart payload could not be normalized")
        return points


class StooqProvider(DataProvider):
    name = "stooq"

    def _to_stooq_symbol(self, symbol: str) -> str:
        cleaned = symbol.strip().lower()
        if "." in cleaned:
            return cleaned
        return f"{cleaned}.us"

    def _parse_csv(self, text: str) -> Tuple[List[str], List[List[str]]]:
        lines = [line for line in text.strip().splitlines() if line.strip()]
        if len(lines) < 2:
            raise ProviderError("Stooq returned insufficient CSV rows")
        header = [col.strip() for col in lines[0].split(",")]
        rows = [[col.strip() for col in line.split(",")] for line in lines[1:]]
        return header, rows

    def get_quotes(self, symbols: Iterable[str]) -> List[Dict[str, Any]]:
        normalized = []
        for symbol in symbols:
            raw_symbol = symbol.strip()
            if not raw_symbol:
                continue
            stooq_symbol = self._to_stooq_symbol(raw_symbol)
            csv_text = _http_get_text(
                "https://stooq.com/q/l/",
                {"s": stooq_symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            )
            header, rows = self._parse_csv(csv_text)
            row_map = dict(zip(header, rows[0]))

            close_raw = row_map.get("Close")
            volume_raw = row_map.get("Volume")
            if close_raw in (None, "N/D", ""):
                raise ProviderError(f"Stooq has no quote for {raw_symbol}")

            normalized.append(
                {
                    "symbol": raw_symbol.upper(),
                    "price": float(close_raw),
                    "changePercent": None,
                    "volume": None if volume_raw in (None, "", "N/D") else int(volume_raw),
                    "source": self.name,
                    "asOf": datetime.now(timezone.utc).isoformat(),
                }
            )

        if not normalized:
            raise ProviderError("Stooq returned no quote data")
        return normalized

    def get_chart(self, symbol: str, interval: str, chart_range: str) -> List[Dict[str, Any]]:
        interval_map = {"1d": "d", "1wk": "w", "1mo": "m"}
        stooq_interval = interval_map.get(interval, "d")

        csv_text = _http_get_text(
            "https://stooq.com/q/d/l/",
            {"s": self._to_stooq_symbol(symbol), "i": stooq_interval},
        )
        header, rows = self._parse_csv(csv_text)

        now = datetime.now(timezone.utc)
        cutoff = _cutoff_from_range(chart_range, now)

        points = []
        for row in rows:
            row_map = dict(zip(header, row))
            date_raw = row_map.get("Date")
            close_raw = row_map.get("Close")
            volume_raw = row_map.get("Volume")
            if not date_raw or close_raw in (None, "", "N/D"):
                continue

            ts = datetime.strptime(date_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if cutoff and ts < cutoff:
                continue

            points.append(
                {
                    "time": ts.isoformat(),
                    "close": float(close_raw),
                    "volume": None if volume_raw in (None, "", "N/D") else int(volume_raw),
                    "source": self.name,
                }
            )

        if not points:
            raise ProviderError("Stooq returned no chart rows after normalization")
        return points


class AlphaVantageProvider(DataProvider):
    name = "alpha_vantage"

    def __init__(self, api_key: str = "demo") -> None:
        self.api_key = api_key

    def _request(self, params: Dict[str, str]) -> Dict[str, Any]:
        full_params = {**params, "apikey": self.api_key}
        data = _http_get_json(
            "https://www.alphavantage.co/query",
            full_params,
        )
        if "Error Message" in data:
            raise ProviderError(data["Error Message"])
        if "Note" in data:
            raise ProviderError(data["Note"])
        return data

    def get_quotes(self, symbols: Iterable[str]) -> List[Dict[str, Any]]:
        normalized = []
        for symbol in symbols:
            ticker = symbol.strip().upper()
            if not ticker:
                continue
            payload = self._request({"function": "GLOBAL_QUOTE", "symbol": ticker})
            quote = payload.get("Global Quote", {})
            price = quote.get("05. price")
            if not price:
                raise ProviderError(f"Alpha Vantage returned no quote for {ticker}")

            normalized.append(
                {
                    "symbol": quote.get("01. symbol", ticker),
                    "price": float(price),
                    "changePercent": _parse_percent(quote.get("10. change percent")),
                    "volume": _safe_int(quote.get("06. volume")),
                    "source": self.name,
                    "asOf": datetime.now(timezone.utc).isoformat(),
                }
            )

        if not normalized:
            raise ProviderError("Alpha Vantage returned no quote data")
        return normalized

    def get_chart(self, symbol: str, interval: str, chart_range: str) -> List[Dict[str, Any]]:
        ticker = symbol.strip().upper()
        if interval in {"1m", "5m", "15m", "30m", "60m"}:
            payload = self._request(
                {
                    "function": "TIME_SERIES_INTRADAY",
                    "symbol": ticker,
                    "interval": interval,
                    "outputsize": "compact",
                }
            )
            series_key = f"Time Series ({interval})"
            series = payload.get(series_key, {})
        else:
            payload = self._request(
                {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": ticker,
                    "outputsize": "compact",
                }
            )
            series = payload.get("Time Series (Daily)", {})

        cutoff = _cutoff_from_range(chart_range, datetime.now(timezone.utc))

        points = []
        for ts_raw, values in series.items():
            ts = _parse_av_timestamp(ts_raw)
            if cutoff and ts < cutoff:
                continue
            points.append(
                {
                    "time": ts.isoformat(),
                    "close": float(values.get("4. close")),
                    "volume": _safe_int(values.get("5. volume")),
                    "source": self.name,
                }
            )

        points.sort(key=lambda x: x["time"])
        if not points:
            raise ProviderError("Alpha Vantage returned no chart data")
        return points


def _parse_percent(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(str(value).replace("%", ""))


def _safe_int(value: Any) -> int | None:
    if value in (None, "", "N/D"):
        return None
    return int(float(value))


def _parse_av_timestamp(ts_raw: str) -> datetime:
    fmt = "%Y-%m-%d %H:%M:%S" if " " in ts_raw else "%Y-%m-%d"
    return datetime.strptime(ts_raw, fmt).replace(tzinfo=timezone.utc)


def _cutoff_from_range(chart_range: str, now: datetime) -> datetime | None:
    mapping = {
        "1d": timedelta(days=1),
        "5d": timedelta(days=5),
        "1mo": timedelta(days=30),
        "3mo": timedelta(days=90),
        "6mo": timedelta(days=180),
        "1y": timedelta(days=365),
        "2y": timedelta(days=730),
        "5y": timedelta(days=1825),
        "10y": timedelta(days=3650),
    }
    delta = mapping.get(chart_range)
    return None if not delta else now - delta


PROVIDERS: List[DataProvider] = [
    YahooProvider(),
    StooqProvider(),
    AlphaVantageProvider(),
]


def get_quotes(symbols: Iterable[str]) -> Tuple[ProviderResult | None, List[Dict[str, str]]]:
    errors: List[Dict[str, str]] = []

    for provider in PROVIDERS:
        try:
            return ProviderResult(provider=provider.name, data=provider.get_quotes(symbols)), errors
        except Exception as exc:
            errors.append({"provider": provider.name, "message": str(exc)})

    return None, errors


def get_chart(symbol: str, interval: str, chart_range: str) -> Tuple[ProviderResult | None, List[Dict[str, str]]]:
    errors: List[Dict[str, str]] = []

    for provider in PROVIDERS:
        try:
            return ProviderResult(
                provider=provider.name,
                data=provider.get_chart(symbol, interval, chart_range),
            ), errors
        except Exception as exc:
            errors.append({"provider": provider.name, "message": str(exc)})

    return None, errors


@app.route("/api/quotes")
def quotes_endpoint():
    from flask import request

    symbols_param = request.args.get("symbols", "")
    symbols = [s.strip() for s in symbols_param.split(",") if s.strip()]
    if not symbols:
        return jsonify({"error": "Query param 'symbols' is required"}), 400

    result, errors = get_quotes(symbols)
    if result is None:
        return (
            jsonify(
                {
                    "error": "All quote providers failed",
                    "provider": None,
                    "fallbackUsed": False,
                    "errors": errors,
                }
            ),
            502,
        )

    return jsonify(
        {
            "provider": result.provider,
            "fallbackUsed": result.provider != PROVIDERS[0].name,
            "errors": errors,
            "data": result.data,
        }
    )


@app.route("/api/chart/<ticker>")
def chart_endpoint(ticker: str):
    from flask import request

    interval = request.args.get("interval", "1d")
    chart_range = request.args.get("range", "1mo")

    result, errors = get_chart(ticker, interval, chart_range)
    if result is None:
        return (
            jsonify(
                {
                    "error": "All chart providers failed",
                    "provider": None,
                    "fallbackUsed": False,
                    "errors": errors,
                }
            ),
            502,
        )

    return jsonify(
        {
            "provider": result.provider,
            "fallbackUsed": result.provider != PROVIDERS[0].name,
            "errors": errors,
            "data": result.data,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
