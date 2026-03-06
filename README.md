# iGaruda Terminal (SAT SET)

Kalau kamu nggak mau ribet deploy, command panjang, atau setup aneh-aneh:

## Cara pakai paling gampang (1 langkah)

```bash
./run_igaruda.sh
```

Lalu langsung buka link ini di browser:

- <http://127.0.0.1:4173>

Selesai. Kalau mau stop tinggal tekan `CTRL + C` di terminal.

---

## Kalau `run_igaruda.sh` belum bisa dieksekusi

Jalankan sekali ini:

```bash
chmod +x run_igaruda.sh
./run_igaruda.sh
```

---

## Data realtime

- App ini ambil data live dari feed market publik simbol Indonesia (`*.JK`) via backend `server.py`.
- **Tidak pakai dummy/fallback angka harga.**
- Kalau feed eksternal lagi error/terblokir, UI akan tampilkan `LIVE FEED ERROR` secara transparan.

---

## File penting

- `run_igaruda.sh` → launcher instan (yang kamu pakai)
- `server.py` → backend API live data
- `index.html`, `styles.css`, `script.js` → tampilan terminal
