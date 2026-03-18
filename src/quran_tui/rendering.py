from __future__ import annotations

import os
import re

from ._vendor import arabic_reshaper
from ._vendor.bidi.algorithm import get_display

ARABIC_RUN_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF ]+"
)
RLM = "\u200f"


ARABIC_DISPLAY_MODES = {"plain", "bidi", "reshaped"}
DEFAULT_ARABIC_DISPLAY_MODE = os.environ.get("QURAN_TUI_ARABIC_MODE", "bidi").strip().lower()
if DEFAULT_ARABIC_DISPLAY_MODE not in ARABIC_DISPLAY_MODES:
    DEFAULT_ARABIC_DISPLAY_MODE = "bidi"


def prepare_terminal_text(text: str) -> str:
    """Prepare Arabic text for terminals with different bidi/shaping behavior."""
    return prepare_terminal_text_with_mode(text, DEFAULT_ARABIC_DISPLAY_MODE)


def prepare_terminal_text_with_mode(text: str, mode: str) -> str:
    if not text:
        return text
    return ARABIC_RUN_RE.sub(lambda match: _transform_run(match, mode), text)


def _transform_run(match: re.Match[str], mode: str) -> str:
    value = match.group(0)
    if not any(_is_arabic_char(char) for char in value):
        return value
    if mode == "plain":
        return f"{RLM}{value}{RLM}"
    if mode == "bidi":
        return get_display(value)
    return get_display(arabic_reshaper.reshape(value))


def _is_arabic_char(char: str) -> bool:
    codepoint = ord(char)
    return (
        0x0600 <= codepoint <= 0x06FF
        or 0x0750 <= codepoint <= 0x077F
        or 0x08A0 <= codepoint <= 0x08FF
        or 0xFB50 <= codepoint <= 0xFDFF
        or 0xFE70 <= codepoint <= 0xFEFF
    )
