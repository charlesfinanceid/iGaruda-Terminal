#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-4173}"
HOST="${HOST:-127.0.0.1}"
URL="http://${HOST}:${PORT}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 tidak ditemukan. Install Python 3 dulu ya."
  exit 1
fi

echo "============================================"
echo " iGaruda Terminal — SAT SET MODE"
echo "============================================"
echo "1) Server akan jalan otomatis"
echo "2) Buka link ini di browser: ${URL}"
echo "3) Stop server: tekan CTRL+C"
echo ""

# Jalankan server langsung (foreground) biar simpel untuk user non-teknis.
exec python3 server.py
