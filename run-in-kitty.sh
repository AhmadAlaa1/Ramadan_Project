#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export QURAN_TUI_ARABIC_MODE="${QURAN_TUI_ARABIC_MODE:-bidi}"
export QURAN_TUI_AUTO_KITTY=1

exec kitty \
  --title "DuaTerm" \
  sh -lc "cd '$ROOT_DIR' && python3 main.py"
