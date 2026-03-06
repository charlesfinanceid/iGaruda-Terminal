# iGaruda-Terminal

Layanan API sederhana untuk iGaruda-Terminal.

## Health Check

- `GET /health` → endpoint liveness check.
  - Response: `200 OK`
  - Body JSON:

    ```json
    {
      "status": "ok",
      "service": "iGaruda-Terminal"
    }
    ```

- `GET /ready` → endpoint readiness check (opsional).
  - Jika `UPSTREAM_HEALTH_URL` diset, endpoint ini akan melakukan pengecekan dependency upstream minimal.
  - Jika upstream gagal, response menjadi `503` dengan detail status dependency.

## Menjalankan Lokal

```bash
pip install flask
python server.py
```

Default URL: `http://localhost:8000`
