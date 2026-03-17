from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .model import SurahDetails
from .theme import get_render_theme

DEFAULT_FONT_PATH = "/usr/share/fonts/google-noto-vf/NotoNaskhArabic[wght].ttf"
DEFAULT_UI_FONT_PATH = "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf"
RENDER_VERSION = "21"
BASMALA_PREFIXES = (
    "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
)


class KittyAyahRenderer:
    def __init__(
        self,
        font_path: str = DEFAULT_FONT_PATH,
        ui_font_path: str = DEFAULT_UI_FONT_PATH,
    ) -> None:
        self.font_path = font_path
        self.ui_font_path = ui_font_path
        self.theme = get_render_theme()
        self._theme_signature = tuple(self.theme.__dict__.values())
        self._last_theme_check = 0.0
        self.cache_dir = Path(tempfile.gettempdir()) / "quran-tui-images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_image: Path | None = None
        self.last_place: str | None = None
        self._line_cache: dict[tuple[int, int], list[str]] = {}
        self.title_font = ImageFont.truetype(self.font_path, 34)
        self.text_font = ImageFont.truetype(self.font_path, 29)
        try:
            self.num_font = ImageFont.truetype(self.ui_font_path, 22)
            self.meta_font = ImageFont.truetype(self.ui_font_path, 20)
        except OSError:
            self.num_font = ImageFont.load_default()
            self.meta_font = ImageFont.load_default()
        self.basmala_font = ImageFont.truetype(self.font_path, 38)
        self.ornament_font = ImageFont.truetype(self.font_path, 24)

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
        width_px = max(400, width_cells * 14)
        width_px = max(420, int((width_px - 40) * 0.72))
        extra_lines = 2 if self._extract_basmala(surah) else 0
        return len(self._get_wrapped_lines(surah, width_px)) + extra_lines

    def get_visible_line_count(self, surah: SurahDetails, width_cells: int, height_cells: int) -> int:
        width_px = max(400, width_cells * 14)
        height_px = max(240, height_cells * 28)
        outer_margin_y = 18
        y = outer_margin_y + 112
        line_height = 42
        if self._extract_basmala(surah):
            y += line_height * 3 + 10
        return max(1, (height_px - y - 38) // line_height)

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
        self._refresh_theme_if_needed()

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
            f"{RENDER_VERSION}:{self._theme_signature}:{surah.summary.number}:{top_line}:{width_cells}:{height_cells}:{content}".encode("utf-8")
        ).hexdigest()
        image_path = self.cache_dir / f"{key}.png"
        if image_path.exists():
            return image_path

        cell_px_w = 14
        cell_px_h = 28
        width_px = max(400, width_cells * cell_px_w)
        height_px = max(240, height_cells * cell_px_h)
        outer_margin_x = 20
        outer_margin_y = 18

        image = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (
                outer_margin_x,
                outer_margin_y,
                width_px - outer_margin_x,
                height_px - outer_margin_y,
            ),
            radius=18,
            fill=(0, 0, 0, 0),
            outline=(240, 236, 228, 110),
            width=2,
        )
        page_margin_x = 52
        header_left_x = outer_margin_x + page_margin_x
        header_center_x = width_px // 2

        title = surah.summary.arabic_name
        title_ornament = "۞ ۞ ۞"
        draw.text(
            (header_center_x, outer_margin_y + 8),
            title_ornament,
            font=self.ornament_font,
            fill="#e8dfcf",
            anchor="ma",
            direction="rtl",
            language="ar",
        )
        draw.text(
            (header_center_x, outer_margin_y + 40),
            title,
            font=self.title_font,
            fill=self.theme.header,
            anchor="ma",
            direction="rtl",
            language="ar",
        )
        draw.text(
            (header_center_x, outer_margin_y + 84),
            title_ornament,
            font=self.ornament_font,
            fill="#e8dfcf",
            anchor="ma",
            direction="rtl",
            language="ar",
        )
        draw.text(
            (header_left_x, outer_margin_y + 42),
            f"{surah.summary.number}. {surah.summary.english_name}",
            font=self.num_font,
            fill=self.theme.subheader,
            anchor="la",
        )
        draw.text(
            (header_left_x, outer_margin_y + 70),
            f"{surah.summary.number_of_ayahs} ayahs | {surah.summary.revelation_type}",
            font=self.meta_font,
            fill=self.theme.subheader,
            anchor="la",
        )

        y = outer_margin_y + 124
        line_height = 42
        available_width = max(420, int((width_px - (outer_margin_x * 2)) * 0.72))
        content_center_x = width_px // 2

        basmala = self._extract_basmala(surah)
        if basmala and top_line <= 1:
            ornament_y = y
            basmala_y = y + 32
            ornament = "۞ " * 5
            draw.text(
                (width_px // 2, ornament_y),
                ornament.strip(),
                font=self.ornament_font,
                fill="#e8dfcf",
                anchor="ma",
                direction="rtl",
                language="ar",
            )
            draw.text(
                (width_px // 2, basmala_y),
                basmala,
                font=self.basmala_font,
                fill=self.theme.header,
                anchor="ma",
                direction="rtl",
                language="ar",
            )
            draw.text(
                (width_px // 2, basmala_y + 34),
                ornament.strip(),
                font=self.ornament_font,
                fill="#e8dfcf",
                anchor="ma",
                direction="rtl",
                language="ar",
            )
            # Keep the basmala visually separate from the ayah body.
            y += line_height * 3 + 22

        all_lines = self._get_wrapped_lines(surah, available_width)
        line_offset = max(0, top_line - (2 if basmala else 0))
        visible_line_count = max(1, (height_px - y - 38) // line_height)
        visible_lines = all_lines[line_offset : line_offset + visible_line_count]

        for line_text in visible_lines:
            draw.text(
                (content_center_x, y),
                line_text,
                font=self.text_font,
                fill=self.theme.text,
                anchor="ma",
                direction="rtl",
                language="ar",
            )
            y += line_height

        image.save(image_path)
        return image_path

    def _refresh_theme_if_needed(self) -> None:
        now = time.monotonic()
        if now - self._last_theme_check < 1.0:
            return
        self._last_theme_check = now
        theme = get_render_theme()
        signature = tuple(theme.__dict__.values())
        if signature == self._theme_signature:
            return
        self.theme = theme
        self._theme_signature = signature
        self.last_image = None
        self.last_place = None

    def _extract_basmala(self, surah: SurahDetails) -> str | None:
        if not surah.ayahs:
            return None
        first_ayah = surah.ayahs[0].text.strip()
        for prefix in BASMALA_PREFIXES:
            if first_ayah.startswith(prefix):
                return prefix
        return None

    def _strip_basmala_prefix(self, text: str) -> str:
        for prefix in BASMALA_PREFIXES:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
        return text

    def _get_wrapped_lines(self, surah: SurahDetails, width_px: int) -> list[str]:
        cache_key = (surah.summary.number, width_px)
        cached = self._line_cache.get(cache_key)
        if cached is not None:
            return cached

        image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        lines = self._build_lines(surah, draw, self.text_font, width_px)
        self._line_cache[cache_key] = lines
        return lines

    def _build_lines(self, surah: SurahDetails, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, width_px: int) -> list[str]:
        lines: list[str] = []
        basmala = self._extract_basmala(surah)
        for index, ayah in enumerate(surah.ayahs):
            ayah_text = ayah.text.strip()
            if index == 0 and basmala:
                ayah_text = self._strip_basmala_prefix(ayah_text)
                if not ayah_text:
                    continue
            marker = f" ۝ {self._to_arabic_indic_number(ayah.number_in_surah)}"
            wrapped = self._wrap_arabic_text(draw, ayah_text, font, width_px, suffix=marker)
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


def _hex_to_rgba(value: str, alpha: int) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        return (0, 0, 0, alpha)
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
        alpha,
    )
