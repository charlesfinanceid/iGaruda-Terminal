# iGaruda Terminal

Terminal analitik pasar saham Indonesia (IDX) dengan desain institutional dark-mode dan **live polling per detik**.

## Status data

- Aplikasi ini **hanya menampilkan live data** dari upstream feed (`*.JK`).
- Jika upstream gagal/terblokir, sistem menampilkan **LIVE FEED ERROR** (tanpa data dummy/fallback).

## Endpoint backend

- `GET /api/quotes?symbols=BBCA.JK,BBRI.JK,...`
- `GET /api/chart/:ticker?range=1d&interval=1m`
- `GET /api/news` (target connector resmi IDX/OJK/BI)

## Jalankan lokal

```bash
python3 server.py
```

Lalu buka link ini:
- <http://localhost:4173>

## Bikin link publik yang bisa diklik

Contoh (pakai cloudflared):

```bash
cloudflared tunnel --url http://localhost:4173
```

Nanti akan keluar URL publik `https://...trycloudflare.com` yang bisa langsung dibuka dari device mana pun.
