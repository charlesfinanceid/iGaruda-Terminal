#!/usr/bin/env bash
set -euo pipefail

LOCAL_URL="http://localhost:8080"
PUBLIC_URL="https://igaruda-terminal.vercel.app"

echo "iGaruda Terminal siap digunakan."
echo ""
echo "Versi lokal (untuk perangkat ini):"
echo "👉 Klik link ini: ${LOCAL_URL}"
echo ""
echo "Versi publik (bisa diakses dari mana saja):"
echo "🌍 Klik link ini: ${PUBLIC_URL}"
