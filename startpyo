#!/usr/bin/env bash
# Start the HAMO AI backend (Termux-friendly).
cd "$(dirname "$0")" || exit 1
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock   # keeps Termux alive while you use other apps
fi
exec python backend/main.py
