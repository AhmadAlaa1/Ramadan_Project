from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class RenderTheme:
    background: str
    page: str
    text: str
    number: str
    header: str
    subheader: str
    ornament: str


THEMES: dict[str, RenderTheme] = {
    "dark": RenderTheme(
        background="#655c54",
        page="#716860",
        text="#f2ede4",
        number="#dcca76",
        header="#f6f0e7",
        subheader="#d6c7b8",
        ornament="#cdbb93",
    ),
    "light": RenderTheme(
        background="#d8d0c5",
        page="#efe6da",
        text="#352f2a",
        number="#8f6d17",
        header="#2f2924",
        subheader="#62564d",
        ornament="#9d8451",
    ),
    "forest": RenderTheme(
        background="#161b16",
        page="#222922",
        text="#eef3e7",
        number="#b7c98a",
        header="#f4f7ef",
        subheader="#b6c0ae",
        ornament="#8fa56b",
    ),
    "sand": RenderTheme(
        background="#7c7367",
        page="#8c8378",
        text="#fff9f0",
        number="#ead38a",
        header="#fffdf8",
        subheader="#e4d7c6",
        ornament="#dcc08b",
    ),
}


def get_render_theme() -> RenderTheme:
    theme_name = os.environ.get("QURAN_TUI_THEME", "auto").strip().lower()
    if theme_name == "auto":
        kitty_theme = _get_kitty_render_theme()
        if kitty_theme is not None:
            return kitty_theme
    base = THEMES[_resolve_theme_name(theme_name)]

    return RenderTheme(
        background=os.environ.get("QURAN_TUI_BG", base.background),
        page=os.environ.get("QURAN_TUI_PAGE", base.page),
        text=os.environ.get("QURAN_TUI_TEXT", base.text),
        number=os.environ.get("QURAN_TUI_NUMBER", base.number),
        header=os.environ.get("QURAN_TUI_HEADER", base.header),
        subheader=os.environ.get("QURAN_TUI_SUBHEADER", base.subheader),
        ornament=os.environ.get("QURAN_TUI_ORNAMENT", base.ornament),
    )


def _resolve_theme_name(theme_name: str) -> str:
    if theme_name in THEMES:
        return theme_name
    if theme_name != "auto":
        return "dark"
    return "light" if _terminal_background_is_light() else "forest"


def _terminal_background_is_light() -> bool:
    colorfgbg = os.environ.get("COLORFGBG", "")
    if ";" not in colorfgbg:
        return False
    try:
        bg = int(colorfgbg.split(";")[-1])
    except ValueError:
        return False
    return bg in {7, 15}


def _get_kitty_render_theme() -> RenderTheme | None:
    if not os.environ.get("KITTY_WINDOW_ID"):
        return None
    try:
        result = subprocess.run(
            ["kitty", "@", "get-colors"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    colors: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1].startswith("#"):
            colors[parts[0]] = parts[1]

    background = colors.get("background")
    foreground = colors.get("foreground")
    if not background or not foreground:
        return None

    accent = (
        colors.get("color10")
        or colors.get("color2")
        or colors.get("selection_background")
        or _mix_hex(background, foreground, 0.35)
    )
    return RenderTheme(
        background=background,
        page=_mix_hex(background, foreground, 0.08),
        text=foreground,
        number=_mix_hex(accent, foreground, 0.35),
        header=_mix_hex(foreground, "#ffffff", 0.2),
        subheader=_mix_hex(foreground, background, 0.38),
        ornament=accent,
    )


def _mix_hex(color_a: str, color_b: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    a = _hex_to_rgb(color_a)
    b = _hex_to_rgb(color_b)
    mixed = tuple(int((1 - ratio) * av + ratio * bv) for av, bv in zip(a, b))
    return _rgb_to_hex(mixed)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        return (0, 0, 0)
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)
