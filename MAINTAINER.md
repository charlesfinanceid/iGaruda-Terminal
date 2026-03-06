# Maintainer Notes

## Smoke Check Endpoint Online

Setelah deploy, jalankan validasi singkat untuk memastikan layanan publik aktif.

### 1) Cek endpoint health

```bash
curl -fsS https://igaruda-terminal.vercel.app/health
```

Ekspektasi:
- HTTP 200
- Respons menunjukkan status sehat (misalnya `ok`, `healthy`, atau JSON status serupa)

### 2) Cek endpoint halaman utama

```bash
curl -I -fsS https://igaruda-terminal.vercel.app/
```

Ekspektasi:
- HTTP 200
- Header respons normal dari platform deploy

### 3) Cek manual via browser

- Buka URL publik.
- Pastikan halaman utama tampil normal.
- Pastikan pengguna akhir bisa membaca ajakan sederhana: **"klik link ini"** untuk akses.
