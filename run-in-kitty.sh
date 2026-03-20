#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export NOORTERM_ARABIC_MODE="${NOORTERM_ARABIC_MODE:-${QURAN_TUI_ARABIC_MODE:-bidi}}"
export NOORTERM_AUTO_KITTY=1

exec kitty \
  --title "NoorTerm" \
  sh -lc "cd '$ROOT_DIR' && python3 main.py"
