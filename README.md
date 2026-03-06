# iGaruda-Terminal

Starter deployment configuration for running `server.py` on platforms like Render.

## Live URL

Setelah deploy berhasil, isi URL live app di sini:

- `https://<your-service-name>.onrender.com`

## Deploy 1-klik dari GitHub (Render)

1. Push repo ini ke GitHub.
2. Login ke Render, lalu pilih **New +** → **Blueprint**.
3. Connect repository GitHub yang berisi project ini.
4. Render akan membaca `render.yaml` otomatis, lalu klik **Apply**.
5. Tunggu proses build selesai, lalu buka URL service yang diberikan Render.

## Local Run

```bash
pip install -r requirements.txt
python3 server.py
```

Default binding:
- `HOST=0.0.0.0`
- `PORT=10000`

Health check endpoint:
- `/healthz`
