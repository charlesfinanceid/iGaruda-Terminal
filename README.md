# iGaruda Terminal Backend

Backend Python sederhana yang siap dideploy ke platform PaaS seperti Render, Railway, dan Fly.io agar berjalan 24/7 dengan URL HTTPS publik.

## Live URL

> Isi setelah deployment berhasil:
>
> `https://your-app-name.onrender.com` atau domain publik setara dari Railway/Fly.io.

## Menjalankan lokal

```bash
python3 server.py
```

Endpoint:
- `GET /` → info service
- `GET /health` → health check (`200 {"status":"ok"}`)

## Deploy (1 halaman ringkas)

### Prasyarat
- Repo ini sudah di-push ke GitHub.
- Aplikasi menggunakan command start dari `Procfile`: `web: python3 server.py`.
- Server bind ke `0.0.0.0` dan baca `PORT` dari environment.

### Opsi A — Render
1. Buka [Render Dashboard](https://dashboard.render.com/).
2. Klik **New +** → **Web Service**.
3. Pilih **Connect account GitHub** lalu pilih repo ini.
4. Konfigurasi cepat:
   - Runtime: **Python 3**
   - Build Command: *(boleh kosong / default)*
   - Start Command: `python3 server.py` *(atau biarkan pakai Procfile)*
5. Klik **Create Web Service**.
6. Setelah status **Live**, salin URL HTTPS publik dan tempel ke bagian **Live URL** di README ini.

Deploy tombol cepat:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Opsi B — Railway
1. Buka [Railway](https://railway.app/) dan login.
2. Klik **New Project** → **Deploy from GitHub repo**.
3. Pilih repo ini.
4. Railway akan mendeteksi Python app, lalu gunakan start command:
   - `python3 server.py`
5. Setelah deploy sukses, buka domain generated Railway dan salin URL HTTPS.
6. Tempel URL tersebut ke bagian **Live URL** di README ini.

Deploy tombol cepat:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

### Opsi C — Fly.io
1. Install CLI Fly.io dan login:
   ```bash
   fly auth login
   ```
2. Di root project, inisialisasi app:
   ```bash
   fly launch
   ```
3. Pastikan command menjalankan:
   ```bash
   python3 server.py
   ```
4. Deploy:
   ```bash
   fly deploy
   ```
5. Ambil URL HTTPS dari output deploy, lalu tempel ke bagian **Live URL** di README ini.

## Health check untuk platform

Gunakan endpoint berikut untuk health check platform hosting:

- `GET /health`

Response sukses:

```json
{"status":"ok"}
```
