#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 4173

DEFAULT_TICKERS = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK", "ANTM.JK", "ADRO.JK", "GOTO.JK"]

FALLBACK_QUOTES = [
    {"symbol": "BBCA.JK", "shortName": "Bank Central Asia", "regularMarketPrice": 10175, "regularMarketChangePercent": 1.35, "regularMarketVolume": 115000000},
    {"symbol": "BBRI.JK", "shortName": "Bank Rakyat Indonesia", "regularMarketPrice": 5475, "regularMarketChangePercent": -0.72, "regularMarketVolume": 98000000},
    {"symbol": "TLKM.JK", "shortName": "Telkom Indonesia", "regularMarketPrice": 4210, "regularMarketChangePercent": 0.95, "regularMarketVolume": 76000000},
    {"symbol": "ANTM.JK", "shortName": "Aneka Tambang", "regularMarketPrice": 1810, "regularMarketChangePercent": 2.21, "regularMarketVolume": 102000000},
]


def fetch_json(url: str, timeout: int = 10):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; iGarudaTerminal/1.0)",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, payload, code=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/quotes":
            query = urllib.parse.parse_qs(parsed.query)
            symbols = query.get("symbols", [",".join(DEFAULT_TICKERS)])[0]
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(symbols)}"
            try:
                data = fetch_json(url)
                results = data.get("quoteResponse", {}).get("result", [])
                self._send_json({
                    "mode": "live",
                    "source": "Yahoo Finance (public market feed for IDX symbols)",
                    "asOf": int(time.time()),
                    "results": results,
                })
            except Exception as exc:
                self._send_json({
                    "mode": "fallback",
                    "source": "Fallback sample (external feed blocked)",
                    "asOf": int(time.time()),
                    "error": str(exc),
                    "results": FALLBACK_QUOTES,
                })
            return

        if parsed.path.startswith("/api/chart/"):
            ticker = parsed.path.replace("/api/chart/", "").strip() or "BBCA.JK"
            query = urllib.parse.parse_qs(parsed.query)
            interval = query.get("interval", ["5m"])[0]
            range_val = query.get("range", ["1d"])[0]
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}"
                f"?interval={urllib.parse.quote(interval)}&range={urllib.parse.quote(range_val)}"
            )
            try:
                data = fetch_json(url)
                self._send_json({"mode": "live", "source": "Yahoo Finance chart", "data": data})
            except Exception as exc:
                self._send_json({
                    "mode": "fallback",
                    "source": "Generated fallback chart",
                    "error": str(exc),
                    "data": {
                        "chart": {
                            "result": [{"timestamp": list(range(20)), "indicators": {"quote": [{"close": [100 + i * 0.5 + (i % 3) for i in range(20)]}]}}]
                        }
                    },
                })
            return

        if parsed.path == "/api/news":
            # Placeholder for trusted Indonesian feeds that allow CORS/server-side access.
            self._send_json({
                "mode": "info",
                "source": "IDX / OJK / BI official feeds (connector ready)",
                "items": [
                    "Integrasi resmi: IDX keterbukaan informasi emiten.",
                    "Integrasi resmi: OJK pembaruan regulasi pasar modal.",
                    "Integrasi resmi: Bank Indonesia indikator makro.",
                ],
            })
            return

        return super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"iGaruda Terminal live server running on http://0.0.0.0:{PORT}")
    server.serve_forever()
