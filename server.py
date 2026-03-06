#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.getenv("PORT", "4173"))
HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_TICKERS = [
    "BBCA.JK",
    "BBRI.JK",
    "BMRI.JK",
    "TLKM.JK",
    "ASII.JK",
    "ANTM.JK",
    "ADRO.JK",
    "GOTO.JK",
    "ICBP.JK",
    "UNVR.JK",
]
SECTOR_MAP = {
    "BBCA.JK": "Banking",
    "BBRI.JK": "Banking",
    "BMRI.JK": "Banking",
    "TLKM.JK": "Telecommunications",
    "ASII.JK": "Consumer",
    "ANTM.JK": "Mining",
    "ADRO.JK": "Energy",
    "GOTO.JK": "Technology",
    "ICBP.JK": "Consumer",
    "UNVR.JK": "Consumer",
}
CACHE = {}
CACHE_TTL = 2


def fetch_json(url: str, timeout: int = 10):
    now = time.time()
    cached = CACHE.get(url)
    if cached and now - cached["time"] < CACHE_TTL:
        return cached["data"]

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; iGarudaTerminal/2.0)",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
        CACHE[url] = {"time": now, "data": payload}
        return payload


def quote_url(symbols: str):
    return f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(symbols)}"


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, payload, code=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if self.path.startswith("/api/"):
            return
        super().log_message(format, *args)

    def _normalize_quote(self, item):
        symbol = item.get("symbol", "")
        item["sector"] = SECTOR_MAP.get(symbol, "Unclassified")
        return item

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/quotes":
            symbols = query.get("symbols", [",".join(DEFAULT_TICKERS)])[0]
            url = quote_url(symbols)
            try:
                data = fetch_json(url)
                results = data.get("quoteResponse", {}).get("result", [])
                if not results:
                    raise ValueError("No quote results returned by upstream")
                normalized = [self._normalize_quote(x) for x in results]
                self._send_json(
                    {
                        "mode": "live",
                        "source": "Yahoo Finance public feed (.JK)",
                        "asOf": int(time.time()),
                        "results": normalized,
                    }
                )
            except Exception as exc:
                self._send_json(
                    {
                        "mode": "unavailable",
                        "source": "Yahoo Finance public feed (.JK)",
                        "asOf": int(time.time()),
                        "error": f"Upstream live data unavailable: {exc}",
                        "results": [],
                    },
                    code=502,
                )
            return

        if parsed.path.startswith("/api/chart/"):
            ticker = parsed.path.replace("/api/chart/", "").strip() or "BBCA.JK"
            interval = query.get("interval", ["1m"])[0]
            range_val = query.get("range", ["1d"])[0]
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}"
                f"?interval={urllib.parse.quote(interval)}&range={urllib.parse.quote(range_val)}"
            )
            try:
                data = fetch_json(url)
                result = data.get("chart", {}).get("result", [])
                if not result:
                    raise ValueError("No chart results returned by upstream")
                self._send_json({"mode": "live", "source": "Yahoo Finance chart", "data": data})
            except Exception as exc:
                self._send_json(
                    {
                        "mode": "unavailable",
                        "source": "Yahoo Finance chart",
                        "error": f"Upstream live chart unavailable: {exc}",
                        "data": {},
                    },
                    code=502,
                )
            return

        if parsed.path.startswith("/api/company/"):
            ticker = parsed.path.replace("/api/company/", "").strip() or "BBCA.JK"
            symbol = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
            try:
                data = fetch_json(quote_url(symbol))
                q = data.get("quoteResponse", {}).get("result", [])
                if not q:
                    raise ValueError(f"Company data not found for {symbol}")
                item = q[0]
                company = {
                    "symbol": item.get("symbol", symbol),
                    "name": item.get("longName") or item.get("shortName"),
                    "price": item.get("regularMarketPrice"),
                    "changePercent": item.get("regularMarketChangePercent"),
                    "marketCap": item.get("marketCap"),
                    "volume": item.get("regularMarketVolume"),
                    "fiftyTwoWeekLow": item.get("fiftyTwoWeekLow"),
                    "fiftyTwoWeekHigh": item.get("fiftyTwoWeekHigh"),
                    "currency": item.get("currency"),
                    "exchange": item.get("fullExchangeName"),
                    "sector": SECTOR_MAP.get(symbol, "Unclassified"),
                }
                self._send_json(
                    {
                        "mode": "live",
                        "source": "Yahoo Finance quote summary",
                        "asOf": int(time.time()),
                        "company": company,
                    }
                )
            except Exception as exc:
                self._send_json(
                    {
                        "mode": "unavailable",
                        "source": "Yahoo Finance quote summary",
                        "error": f"Company endpoint unavailable: {exc}",
                        "company": {},
                    },
                    code=502,
                )
            return

        if parsed.path == "/api/news":
            self._send_json(
                {
                    "mode": "info",
                    "source": "IDX / OJK / BI official feeds (connector target)",
                    "items": [
                        "IDX: keterbukaan informasi emiten.",
                        "OJK: pembaruan regulasi pasar modal.",
                        "Bank Indonesia: indikator makro dan kebijakan.",
                    ],
                }
            )
            return

        return super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"iGaruda Terminal server running on http://{HOST}:{PORT}")
    server.serve_forever()
