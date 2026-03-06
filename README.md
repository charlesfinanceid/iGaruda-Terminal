# iGaruda Terminal Runtime Hardening

Dokumen ini merangkum penguatan runtime agar aplikasi lebih stabil saat online.

## 1) Auto restart saat crash

Gunakan Docker Compose dengan policy restart:

```bash
cp .env.example .env
docker compose up -d --build
```

`docker-compose.yml` sudah mengaktifkan `restart: unless-stopped` agar container otomatis naik lagi setelah crash/reboot.

## 2) Reverse proxy + TLS + static caching

- Contoh konfigurasi Nginx ada di `deploy/nginx.conf`.
- Proxy melakukan TLS termination (`listen 443 ssl`) dan forwarding ke app Python di `127.0.0.1:8000`.
- Static assets `index.html`, `styles.css`, `script.js` diberi `Cache-Control` untuk menurunkan beban origin.

> Jika deploy di platform managed (Railway/Render/Fly/Vercel, dll), aktifkan TLS bawaan platform dan atur cache header yang sama untuk static files.

## 3) Timeout upstream + pembatasan refresh

`server.py` menambahkan:

- `UPSTREAM_TIMEOUT` di `fetch_json(...)` untuk mencegah request upstream menggantung.
- `QUOTE_REFRESH_MS` untuk menahan frekuensi fetch ke provider quote (request dibatasi lewat cache in-memory).
- fallback stale-cache jika upstream gagal tapi cache lama masih tersedia.

## 4) Health endpoint

Endpoint `GET /health` mengembalikan `200` + JSON sederhana, cocok untuk health check orchestrator/hosting.

## 5) Environment variables terstruktur

Lihat `.env.example`:

- `HOST`
- `PORT`
- `UPSTREAM_TIMEOUT`
- `QUOTE_REFRESH_MS`
- `QUOTE_PROVIDER_URL` (opsional, default sudah ada)

## 6) Restart & troubleshooting

### Restart service

```bash
docker compose restart
```

### Lihat log

```bash
docker compose logs -f --tail=200
```

### Cek health endpoint

```bash
curl -i http://127.0.0.1:8000/health
```

### Gejala umum

1. **502/timeout ke upstream**
   - Naikkan `UPSTREAM_TIMEOUT` di `.env` (mis. `8` atau `10`).
   - Pastikan DNS/egress VM tidak diblokir.
2. **Traffic tinggi**
   - Naikkan `QUOTE_REFRESH_MS` agar refresh backend lebih jarang.
   - Tambah worker Gunicorn (`--workers`) jika CPU masih longgar.
3. **TLS gagal**
   - Validasi path sertifikat pada Nginx.
   - Jalankan `nginx -t` sebelum reload konfigurasi.

## Menjalankan lokal tanpa Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```
