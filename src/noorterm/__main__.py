from __future__ import annotations

import os
import shlex
import shutil
import sys
from pathlib import Path

from .api import QuranAPI
from .ui import run_app


def _env(name: str, legacy_name: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is not None:
        return value
    if legacy_name is not None:
        return os.environ.get(legacy_name)
    return None


def _repo_root() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src" / "noorterm").exists():
            return parent
    return None


def _maybe_relaunch_in_kitty() -> None:
    if os.environ.get("KITTY_WINDOW_ID"):
        return
    if _env("NOORTERM_AUTO_KITTY", "QURAN_TUI_AUTO_KITTY") == "1":
        return
    if _env("NOORTERM_DISABLE_AUTO_KITTY", "QURAN_TUI_DISABLE_AUTO_KITTY") == "1":
        return
    has_graphical_session = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if not sys.stdout.isatty() and not has_graphical_session:
        return

    kitty = shutil.which("kitty")
    if not kitty:
        return

    env = os.environ.copy()
    env["NOORTERM_AUTO_KITTY"] = "1"

    repo_root = _repo_root()
    if repo_root is not None:
        pythonpath_parts = [str(repo_root / "src")]
        vendor_dir = repo_root / "vendor"
        if vendor_dir.exists():
            pythonpath_parts.append(str(vendor_dir))
        existing = env.get("PYTHONPATH")
        if existing:
            pythonpath_parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    shell_cmd = (
        f"cd {shlex.quote(str(Path.cwd()))} && "
        f"exec {shlex.quote(sys.executable)} -m noorterm"
    )
    os.execvpe(
        kitty,
        [kitty, "--title", "NoorTerm", "sh", "-lc", shell_cmd],
        env,
    )


def main() -> None:
    _maybe_relaunch_in_kitty()
    run_app(QuranAPI())


if __name__ == "__main__":
    main()
