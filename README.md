# iGaruda Terminal

## Live URL
Setelah deploy, aplikasi bisa diakses di URL Render service kamu, misalnya:

- `https://igaruda-terminal.onrender.com`

## Deploy & redeploy singkat
1. Push branch ke GitHub.
2. Hubungkan repository ke Render (Blueprint auto-detect `render.yaml`).
3. Pastikan environment variables berikut terisi di dashboard hosting:
   - `UPSTREAM_TIMEOUT`
   - `CACHE_TTL_SECONDS`
   - `QUOTE_REFRESH_MS`
4. Trigger redeploy dari Render dashboard (Manual Deploy) atau push commit baru (auto deploy aktif).

## Health check
Cek endpoint health:

```bash
curl -i https://<your-live-url>/health
```

Respons sukses:

```json
{"status":"ok"}
```

## Verifikasi pasca deploy
- `/` menampilkan UI utama aplikasi.
- `/health` mengembalikan HTTP 200 + JSON status.
- `/api/quotes` mengembalikan JSON valid.

## Jalankan lokal
```bash
HOST=0.0.0.0 PORT=8000 python3 server.py
```
