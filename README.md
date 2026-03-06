# iGaruda Terminal

iGaruda Terminal adalah dashboard market intelligence untuk saham Indonesia (IDX) dengan mode **live refresh**.

## Yang sudah jalan

- UI terminal profesional dark-mode dengan panel kepadatan tinggi.
- Backend server (`server.py`) dengan endpoint live:
  - `/api/quotes` untuk harga & perubahan saham IDX (symbol `.JK`)
  - `/api/chart/:ticker` untuk data chart intraday
- Frontend auto-refresh setiap 15 detik (live polling).
- Command/search bar untuk load chart ticker cepat.

## Sumber data

- Yahoo Finance public feed untuk simbol IDX (`*.JK`) via backend proxy.
- Struktur sudah disiapkan untuk integrasi feed resmi IDX/OJK/BI.

> Catatan: bila koneksi ke sumber eksternal diblokir lingkungan/server, sistem otomatis masuk mode fallback agar terminal tetap berjalan.

## Jalankan

```bash
python3 server.py
```

Buka: <http://localhost:4173>

## Deploy supaya dapat link publik

Contoh opsi cepat:
- Railway / Render: deploy file ini sebagai Python web service.
- VPS: jalankan `python3 server.py` di belakang Nginx + domain.

Setelah deploy, terminal bisa diakses lewat link publik dan data akan terus refresh.
