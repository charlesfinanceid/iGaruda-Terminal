#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 4173
DEFAULT_TICKERS = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK", "ANTM.JK", "ADRO.JK", "GOTO.JK"]


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
                if not results:
                    raise ValueError("No quote results returned by upstream")
                self._send_json({
                    "mode": "live",
                    "source": "Yahoo Finance public feed (.JK)",
                    "asOf": int(time.time()),
                    "results": results,
                })
            except Exception as exc:
                self._send_json({
                    "mode": "unavailable",
                    "source": "Yahoo Finance public feed (.JK)",
                    "asOf": int(time.time()),
                    "error": f"Upstream live data unavailable: {exc}",
                    "results": [],
                }, code=502)
            return

        if parsed.path.startswith("/api/chart/"):
            ticker = parsed.path.replace("/api/chart/", "").strip() or "BBCA.JK"
            query = urllib.parse.parse_qs(parsed.query)
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
                self._send_json({
                    "mode": "unavailable",
                    "source": "Yahoo Finance chart",
                    "error": f"Upstream live chart unavailable: {exc}",
                    "data": {},
                }, code=502)
            return

        if parsed.path == "/api/news":
            self._send_json({
                "mode": "info",
                "source": "IDX / OJK / BI official feeds (connector target)",
                "items": [
                    "Connector target: IDX keterbukaan informasi emiten.",
                    "Connector target: OJK pembaruan regulasi pasar modal.",
                    "Connector target: Bank Indonesia indikator makro.",
                ],
            })
            return

        return super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"iGaruda Terminal server running on http://0.0.0.0:{PORT}")
    server.serve_forever()
