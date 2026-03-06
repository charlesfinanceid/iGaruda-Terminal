# iGaruda Terminal

Terminal saham Indonesia gaya profesional (dark mode, multi-panel, data refresh live).

## SAT SET (1 langkah)

```bash
./run_igaruda.sh
```

Lalu buka:

- <http://127.0.0.1:4173>

Stop server: `CTRL + C`

---

## Fitur yang sudah jalan

- Watchlist live IDX (`.JK`) dengan refresh quote cepat.
- Heatmap saham, top movers, market breadth, dan ticker feed bawah.
- Chart intraday (1D / 1m) + metrik high/low/intraday return.
- Company snapshot endpoint (`/api/company/:ticker`) untuk detail saham terpilih.
- Command mode sederhana (`top gainers`, `refresh`, atau ketik ticker seperti `BBCA`).
- UI transparan saat upstream gagal: tampil `LIVE FEED ERROR` (tanpa dummy data harga).

---

## Endpoint API backend

- `GET /api/quotes?symbols=BBCA.JK,BBRI.JK`
- `GET /api/chart/BBCA.JK?range=1d&interval=1m`
- `GET /api/company/BBCA.JK`
- `GET /api/news`

Sumber data live saat ini: Yahoo Finance public feed untuk simbol Indonesia (`*.JK`).

---

## Catatan penting

- Jika koneksi ke upstream diblokir environment, backend akan return `502` + pesan error jelas.
- Tidak ada fallback angka palsu untuk harga.
