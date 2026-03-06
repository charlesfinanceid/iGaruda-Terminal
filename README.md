# iGaruda Terminal Backend

Backend ini menyediakan endpoint API sederhana dengan observability minimum:

- Logging JSON terstruktur per request.
- Endpoint metrik `/metrics`.
- Counter fallback usage.
- Konfigurasi level logging via env `LOG_LEVEL`.

## Menjalankan service

```bash
pip install flask
LOG_LEVEL=INFO python server.py
```

## Endpoint

- `GET /health` — healthcheck dasar.
- `GET /generate` — contoh endpoint provider dengan parameter:
  - `provider` (default: `primary`)
  - `cache_hit=true|false`
  - `fallback=true|false`
  - `force_error=true|false`
- `GET /metrics` — metrik runtime:
  - success/fail per provider
  - cache hit ratio
  - fallback usage count

## Runbook Troubleshooting

### 1) Gejala: Request lambat atau timeout

**Cek endpoint:**
- `GET /health`
- Pantau log JSON untuk `latency_ms` tinggi.

**Tindakan cepat:**
- Verifikasi provider upstream sedang sehat.
- Turunkan traffic burst sementara (rate limit/retry backoff).
- Aktifkan fallback provider jika provider utama bermasalah.

### 2) Gejala: Banyak error 5xx

**Cek endpoint:**
- `GET /metrics` untuk `fail_by_provider`.
- Log JSON (`error_class` dan `error_message`).

**Tindakan cepat:**
- Identifikasi provider yang dominan gagal.
- Alihkan request ke provider cadangan.
- Naikkan level log ke `DEBUG` sementara (`LOG_LEVEL=DEBUG`) untuk investigasi.

### 3) Gejala: Cache terasa tidak efektif

**Cek endpoint:**
- `GET /metrics` → `cache.hit_ratio`.

**Tindakan cepat:**
- Cek konsistensi key cache dan TTL.
- Pastikan request dengan payload identik menghasilkan key yang sama.
- Audit invalidation policy agar tidak terlalu agresif.

### 4) Gejala: Fallback sering terpakai

**Cek endpoint:**
- `GET /metrics` → `fallback_usage`.
- `GET /metrics` → `fail_by_provider` untuk provider utama.

**Tindakan cepat:**
- Investigasi reliabilitas provider utama (error rate/latensi).
- Sesuaikan timeout + retry policy provider utama.
- Naikkan porsi traffic provider cadangan secara bertahap sampai stabil.
