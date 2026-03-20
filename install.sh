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

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

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
API_RESPONSE_PATH="${TMP_DIR}/latest-release.json"
API_HEADERS_PATH="${TMP_DIR}/latest-release.headers"

CURL_ARGS=(
  -sSL
  -D "$API_HEADERS_PATH"
  -H "Accept: application/vnd.github+json"
  -H "User-Agent: ${PROJECT_NAME}-installer"
)

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  CURL_ARGS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
elif [[ -n "${GH_TOKEN:-}" ]]; then
  CURL_ARGS+=(-H "Authorization: Bearer ${GH_TOKEN}")
fi

if ! HTTP_STATUS="$(
  curl "${CURL_ARGS[@]}" -o "$API_RESPONSE_PATH" -w '%{http_code}' "$API_URL"
)"; then
  echo "Failed to reach the GitHub API for ${GITHUB_REPO}." >&2
  echo "Check network access, confirm the repo name, or rerun with GITHUB_TOKEN=<token> if access is restricted." >&2
  exit 1
fi

if [[ ! -s "$API_RESPONSE_PATH" ]]; then
  echo "GitHub API returned an empty response while fetching the latest release for ${GITHUB_REPO}." >&2
  echo "If this is a private repo or you are being rate-limited, rerun with GITHUB_TOKEN=<token>." >&2
  exit 1
fi

if [[ "$HTTP_STATUS" != "200" ]]; then
  python3 - "$GITHUB_REPO" "$HTTP_STATUS" "$API_RESPONSE_PATH" <<'PY'
import json
from pathlib import Path
import sys

repo = sys.argv[1]
status = sys.argv[2]
body = Path(sys.argv[3]).read_text(encoding="utf-8", errors="replace").strip()

message = ""
try:
    payload = json.loads(body)
except json.JSONDecodeError:
    payload = None

if isinstance(payload, dict):
    message = payload.get("message", "").strip()

if status == "404":
    if message == "Not Found":
        print(
            f"No published GitHub release was found for {repo}. "
            "Create a release first or point NOORTERM_GITHUB_REPO at a repo with releases.",
            file=sys.stderr,
        )
    else:
        print(f"GitHub API returned 404 for {repo}: {message or body}", file=sys.stderr)
elif status == "403":
    print(
        f"GitHub API returned 403 for {repo}: {message or body or 'access denied or rate limited'}. "
        "Try again with GITHUB_TOKEN=<token>.",
        file=sys.stderr,
    )
else:
    print(f"GitHub API returned HTTP {status} for {repo}: {message or body}", file=sys.stderr)
raise SystemExit(1)
PY
fi

ASSET_URL="$(
  python3 - "$TARGET" "$API_RESPONSE_PATH" <<'PY'
import json
from pathlib import Path
import sys

target = sys.argv[1]
payload_path = Path(sys.argv[2])

try:
    data = json.loads(payload_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(
        f"GitHub API returned invalid JSON while fetching the latest release metadata: {exc}"
    )

if not isinstance(data, dict):
    raise SystemExit("GitHub API returned an unexpected response shape for the latest release.")

message = data.get("message")
if message:
    raise SystemExit(f"GitHub API error: {message}")

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
