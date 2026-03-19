from __future__ import annotations

import os
import shlex
import shutil
import sys
from pathlib import Path

from .api import QuranAPI
from .ui import run_app


def _repo_root() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src" / "quran_tui").exists():
            return parent
    return None


def _maybe_relaunch_in_kitty() -> None:
    if os.environ.get("KITTY_WINDOW_ID"):
        return
    if os.environ.get("QURAN_TUI_AUTO_KITTY") == "1":
        return
    if os.environ.get("QURAN_TUI_DISABLE_AUTO_KITTY") == "1":
        return
    if not sys.stdout.isatty():
        return

    kitty = shutil.which("kitty")
    if not kitty:
        return

    env = os.environ.copy()
    env["QURAN_TUI_AUTO_KITTY"] = "1"

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
        f"exec {shlex.quote(sys.executable)} -m quran_tui"
    )
    os.execvpe(
        kitty,
        [kitty, "--title", "DuaTerm", "sh", "-lc", shell_cmd],
        env,
    )


def main() -> None:
    _maybe_relaunch_in_kitty()
    run_app(QuranAPI())


if __name__ == "__main__":
    main()
