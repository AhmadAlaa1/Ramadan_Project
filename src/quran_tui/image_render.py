from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .model import SurahDetails

DEFAULT_FONT_PATH = "/usr/share/fonts/google-noto-vf/NotoNaskhArabic[wght].ttf"
BG_COLOR = "#655c54"
FG_COLOR = "#f2ede4"
NUMBER_COLOR = "#dcca76"
HEADER_COLOR = "#f6f0e7"
SUBHEADER_COLOR = "#d6c7b8"
RENDER_VERSION = "3"


class KittyAyahRenderer:
    def __init__(self, font_path: str = DEFAULT_FONT_PATH) -> None:
        self.font_path = font_path
        self.cache_dir = Path(tempfile.gettempdir()) / "quran-tui-images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_image: Path | None = None
        self.last_place: str | None = None
        self._line_cache: dict[tuple[int, int], list[str]] = {}

    def is_supported(self) -> bool:
        return bool(os.environ.get("KITTY_WINDOW_ID"))

    def clear(self) -> None:
        if not self.is_supported():
            return
        self.last_image = None
        self.last_place = None
        subprocess.run(
            [
                "kitty",
                "+kitten",
                "icat",
                "--stdin=no",
                "--clear",
                "--unicode-placeholder",
                "--silent",
            ],
            check=False,
            stderr=subprocess.DEVNULL,
        )

    def get_total_lines(self, surah: SurahDetails, width_cells: int) -> int:
        width_px = max(400, width_cells * 14) - (28 * 2)
        return len(self._get_wrapped_lines(surah, width_px))

    def draw(
        self,
        surah: SurahDetails,
        top_line: int,
        width_cells: int,
        height_cells: int,
        x_cell: int,
        y_cell: int,
    ) -> None:
        if not self.is_supported():
            return

        image_path = self._render_image(surah, top_line, width_cells, height_cells)
        place = f"{width_cells}x{height_cells}@{x_cell}x{y_cell}"
        if self.last_image == image_path and self.last_place == place:
            return
        self.last_image = image_path
        self.last_place = place
        subprocess.run(
            [
                "kitty",
                "+kitten",
                "icat",
                "--stdin=no",
                "--unicode-placeholder",
                "--transfer-mode=stream",
                "--place",
                place,
                str(image_path),
            ],
            check=False,
            stderr=subprocess.DEVNULL,
        )

    def _render_image(self, surah: SurahDetails, top_line: int, width_cells: int, height_cells: int) -> Path:
        content = "\n".join(f"{ayah.number_in_surah} {ayah.text}" for ayah in surah.ayahs)
        key = hashlib.sha256(
            f"{RENDER_VERSION}:{surah.summary.number}:{top_line}:{width_cells}:{height_cells}:{content}".encode("utf-8")
        ).hexdigest()
        image_path = self.cache_dir / f"{key}.png"
        if image_path.exists():
            return image_path

        cell_px_w = 14
        cell_px_h = 28
        width_px = max(400, width_cells * cell_px_w)
        height_px = max(240, height_cells * cell_px_h)
        margin_x = 28
        margin_y = 18

        image = Image.new("RGB", (width_px, height_px), BG_COLOR)
        draw = ImageDraw.Draw(image)
        title_font = ImageFont.truetype(self.font_path, 30)
        text_font = ImageFont.truetype(self.font_path, 28)
        num_font = ImageFont.truetype(self.font_path, 22)

        title = surah.summary.arabic_name
        draw.text(
            (width_px - margin_x, margin_y),
            title,
            font=title_font,
            fill=HEADER_COLOR,
            anchor="ra",
            direction="rtl",
            language="ar",
        )
        draw.text(
            (margin_x, margin_y + 4),
            f"{surah.summary.number}. {surah.summary.english_name}",
            font=num_font,
            fill=SUBHEADER_COLOR,
            anchor="la",
        )

        y = margin_y + 38
        line_height = 34
        available_width = width_px - (margin_x * 2)

        all_lines = self._get_wrapped_lines(surah, available_width)
        visible_line_count = max(1, (height_px - y - margin_y) // line_height)
        visible_lines = all_lines[top_line : top_line + visible_line_count]

        for line_text in visible_lines:
            draw.text(
                (width_px - margin_x, y),
                line_text,
                font=text_font,
                fill=FG_COLOR,
                anchor="ra",
                direction="rtl",
                language="ar",
            )
            y += line_height

        image.save(image_path)
        return image_path

    def _get_wrapped_lines(self, surah: SurahDetails, width_px: int) -> list[str]:
        cache_key = (surah.summary.number, width_px)
        cached = self._line_cache.get(cache_key)
        if cached is not None:
            return cached

        image = Image.new("RGB", (16, 16), BG_COLOR)
        draw = ImageDraw.Draw(image)
        text_font = ImageFont.truetype(self.font_path, 28)
        lines = self._build_lines(surah, draw, text_font, width_px)
        self._line_cache[cache_key] = lines
        return lines

    def _build_lines(self, surah: SurahDetails, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, width_px: int) -> list[str]:
        lines: list[str] = []
        for ayah in surah.ayahs:
            marker = f" ۝ {self._to_arabic_indic_number(ayah.number_in_surah)}"
            wrapped = self._wrap_arabic_text(draw, ayah.text, font, width_px, suffix=marker)
            wrapped[-1] = f"{wrapped[-1]}{marker}"
            lines.extend(wrapped)
        return lines

    def _wrap_arabic_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        width_px: int,
        suffix: str = "",
    ) -> list[str]:
        words = text.split()
        if not words:
            return [text]

        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            candidate_for_measure = candidate
            if suffix:
                candidate_for_measure = f"{candidate}{suffix}"
            bbox = draw.textbbox((0, 0), candidate_for_measure, font=font, direction="rtl", language="ar")
            if bbox[2] - bbox[0] <= width_px:
                current = candidate
            else:
                lines.append(current)
                current = word
                suffix = ""
        lines.append(current)
        return lines

    def _to_arabic_indic_number(self, value: int) -> str:
        digits = "٠١٢٣٤٥٦٧٨٩"
        return "".join(digits[int(char)] for char in str(value))
