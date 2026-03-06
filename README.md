# iGaruda-Terminal

Aplikasi backend Python kecil dengan entrypoint langsung dari `server.py`.

## Run lokal

```bash
python3 server.py
```

Variabel environment yang dipakai:

- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `8000`)

## Deploy (contoh: Render)

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn -b 0.0.0.0:$PORT server:app`

## Live URL

Belum tersedia (butuh proses deploy via akun platform hosting).
