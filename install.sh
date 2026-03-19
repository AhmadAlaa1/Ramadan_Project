#!/usr/bin/env bash
set -euo pipefail

APP_NAME="NoorTerm"
PROJECT_NAME="noorterm"
GITHUB_REPO="${NOORTERM_GITHUB_REPO:-AhmadAlaa1/noorterm}"
API_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd curl
require_cmd python3

detect_target() {
  if command -v apt >/dev/null 2>&1; then
    echo "deb"
    return
  fi
  if command -v dnf >/dev/null 2>&1; then
    echo "rpm"
    return
  fi
  if command -v yum >/dev/null 2>&1; then
    echo "rpm"
    return
  fi
  echo ""
}

TARGET="${1:-$(detect_target)}"
if [[ -z "$TARGET" ]]; then
  echo "Unsupported distro. Supported package targets: Debian/Ubuntu (.deb), Fedora/RHEL (.rpm)." >&2
  exit 1
fi

case "$TARGET" in
  deb|rpm) ;;
  *)
    echo "Unknown target '$TARGET'. Use 'deb' or 'rpm'." >&2
    exit 1
    ;;
esac

echo "Fetching latest ${APP_NAME} release metadata from ${GITHUB_REPO}..."
ASSET_URL="$(
  curl -fsSL "$API_URL" | python3 - "$TARGET" <<'PY'
import json
import sys

target = sys.argv[1]
data = json.load(sys.stdin)
assets = data.get("assets", [])

if target == "deb":
    suffix = ".deb"
elif target == "rpm":
    suffix = ".rpm"
else:
    raise SystemExit("unsupported target")

for asset in assets:
    name = asset.get("name", "")
    url = asset.get("browser_download_url", "")
    if name.endswith(suffix):
        print(url)
        raise SystemExit(0)

raise SystemExit(f"No {suffix} asset found in the latest release.")
PY
)"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PACKAGE_PATH="${TMP_DIR}/package.${TARGET}"
echo "Downloading package..."
curl -fL "$ASSET_URL" -o "$PACKAGE_PATH"

if [[ "$TARGET" == "deb" ]]; then
  require_cmd sudo
  require_cmd apt
  echo "Installing ${APP_NAME} package with apt..."
  sudo apt install -y "$PACKAGE_PATH"
else
  require_cmd sudo
  if command -v dnf >/dev/null 2>&1; then
    echo "Installing ${APP_NAME} package with dnf..."
    sudo dnf install -y "$PACKAGE_PATH"
  else
    require_cmd yum
    echo "Installing ${APP_NAME} package with yum..."
    sudo yum install -y "$PACKAGE_PATH"
  fi
fi

echo
echo "${APP_NAME} installed."
echo "Run it with:"
echo "  noorterm"
