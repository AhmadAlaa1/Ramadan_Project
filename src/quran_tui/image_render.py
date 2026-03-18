from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .azkar import Zikr
from .model import SurahDetails
from .theme import get_render_theme

DEFAULT_FONT_PATH = "/usr/share/fonts/google-noto-vf/NotoNaskhArabic[wght].ttf"
DEFAULT_UI_FONT_PATH = "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf"
RENDER_VERSION = "31"
BASMALA_PREFIXES = (
    "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
)
AYAH_MARKER_RE = re.compile(r"\[\[AYAH:(\d+)\]\]")


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
        width_px = max(420, int((width_px - 40) * 0.86))
        extra_lines = 2 if self._extract_basmala(surah) else 0
        return len(self._get_wrapped_lines(surah, width_px)) + extra_lines

    def get_visible_line_count(self, surah: SurahDetails, width_cells: int, height_cells: int) -> int:
        width_px = max(400, width_cells * 14)
        height_px = max(240, height_cells * 28)
        outer_margin_y = 18
        y = outer_margin_y + 112
        line_height = 44
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
            outline=(245, 245, 245, 120),
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
            fill="#f5f5f5",
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
            fill="#f5f5f5",
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

        y = outer_margin_y + 136
        line_height = 44
        available_width = max(500, int((width_px - (outer_margin_x * 2)) * 0.80))
        content_right_x = width_px - outer_margin_x - 68

        basmala = self._extract_basmala(surah)
        if basmala and top_line <= 1:
            ornament_y = y
            basmala_y = y + 32
            ornament = "۞ " * 5
            draw.text(
                (width_px // 2, ornament_y),
                ornament.strip(),
                font=self.ornament_font,
                fill="#f5f5f5",
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
                fill="#f5f5f5",
                anchor="ma",
                direction="rtl",
                language="ar",
            )
            # Keep the basmala visually separate from the ayah body.
            y += line_height * 3 + 28

        all_lines = self._get_wrapped_lines(surah, available_width)
        line_offset = max(0, top_line - (2 if basmala else 0))
        visible_line_count = max(1, (height_px - y - 38) // line_height)
        visible_lines = all_lines[line_offset : line_offset + visible_line_count]

        for line_text in visible_lines:
            self._draw_line_with_markers(draw, content_right_x, y, line_text)
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
        token_groups: list[list[str]] = []
        for index, ayah in enumerate(surah.ayahs):
            ayah_text = ayah.text.strip()
            if index == 0 and basmala:
                ayah_text = self._strip_basmala_prefix(ayah_text)
                if not ayah_text:
                    continue
            words = ayah_text.split()
            if not words:
                continue
            token_groups.append(words + [f"[[AYAH:{ayah.number_in_surah}]]"])

        current_tokens: list[str] = []
        for group_index, group in enumerate(token_groups):
            for token in group:
                candidate_tokens = current_tokens + [token]
                candidate_text = " ".join(candidate_tokens)
                if current_tokens and self._measure_mixed_text(draw, candidate_text, font) > width_px:
                    is_last_line = False
                    lines.append(self._justify_arabic_line(draw, current_tokens, font, width_px, is_last_line))
                    current_tokens = [token]
                else:
                    current_tokens = candidate_tokens
            if group_index == len(token_groups) - 1:
                continue
        if current_tokens:
            lines.append(" ".join(current_tokens))
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

    def _justify_arabic_line(
        self,
        draw: ImageDraw.ImageDraw,
        tokens: list[str],
        font: ImageFont.FreeTypeFont,
        width_px: int,
        is_last_line: bool,
    ) -> str:
        text = " ".join(tokens)
        if is_last_line or len(tokens) < 3:
            return text
        if tokens[-1].startswith("[[AYAH:") and tokens[-1].endswith("]]"):
            return text
        current_width = self._measure_mixed_text(draw, text, font)
        if current_width >= width_px * 0.9:
            return text

        space_width = draw.textlength(" ", font=font, direction="rtl", language="ar")
        if space_width <= 0:
            return text

        gaps = len(tokens) - 1
        extra_spaces = int((width_px - current_width) / space_width)
        if extra_spaces <= 0:
            return text
        extra_spaces = min(extra_spaces, gaps * 3)

        base_extra = extra_spaces // gaps
        remainder = extra_spaces % gaps
        parts: list[str] = []
        for index, token in enumerate(tokens[:-1]):
            parts.append(token)
            gap_spaces = 1 + base_extra + (1 if index < remainder else 0)
            parts.append(" " * gap_spaces)
        parts.append(tokens[-1])
        return "".join(parts)

    def _measure_plain_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
    ) -> float:
        return draw.textlength(text, font=font, direction="rtl", language="ar")

    def _draw_line_with_markers(self, draw: ImageDraw.ImageDraw, right_x: int, y: int, text: str) -> None:
        parts: list[tuple[str, str]] = []
        last_end = 0
        for match in AYAH_MARKER_RE.finditer(text):
            if match.start() > last_end:
                parts.append(("text", text[last_end:match.start()]))
            parts.append(("marker", match.group(1)))
            last_end = match.end()
        if last_end < len(text):
            parts.append(("text", text[last_end:]))

        x = float(right_x)
        for kind, value in parts:
            if kind == "text":
                if not value:
                    continue
                draw.text(
                    (x, y),
                    value,
                    font=self.text_font,
                    fill=self.theme.text,
                    anchor="ra",
                    direction="rtl",
                    language="ar",
                )
                x -= self._measure_plain_text(draw, value, self.text_font)
            else:
                label = f"({value})"
                draw.text(
                    (x, y),
                    label,
                    font=self.num_font,
                    fill=self.theme.text,
                    anchor="ra",
                )
                x -= draw.textlength(label, font=self.num_font) + draw.textlength(" ", font=self.num_font)

    def _measure_mixed_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
    ) -> float:
        width = 0.0
        last_end = 0
        for match in AYAH_MARKER_RE.finditer(text):
            if match.start() > last_end:
                width += self._measure_plain_text(draw, text[last_end:match.start()], font)
            label = f"({match.group(1)})"
            width += draw.textlength(label, font=self.num_font) + draw.textlength(" ", font=self.num_font)
            last_end = match.end()
        if last_end < len(text):
            width += self._measure_plain_text(draw, text[last_end:], font)
        return width

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


class KittyAzkarRenderer:
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
        self.cache_dir = Path(tempfile.gettempdir()) / "quran-tui-azkar-images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_image: Path | None = None
        self.last_place: str | None = None
        self.text_font = ImageFont.truetype(self.font_path, 30)
        try:
            self.title_font = ImageFont.truetype(self.ui_font_path, 28)
            self.ui_font = ImageFont.truetype(self.ui_font_path, 22)
            self.ui_font_small = ImageFont.truetype(self.ui_font_path, 18)
        except OSError:
            self.title_font = ImageFont.load_default()
            self.ui_font = ImageFont.load_default()
            self.ui_font_small = ImageFont.load_default()

    def is_supported(self) -> bool:
        return bool(os.environ.get("KITTY_WINDOW_ID"))

    def clear(self) -> None:
        self.last_image = None
        self.last_place = None

    def draw(
        self,
        title: str,
        items: list[Zikr],
        top_index: int,
        selected_index: int,
        width_cells: int,
        height_cells: int,
        x_cell: int,
        y_cell: int,
    ) -> None:
        if not self.is_supported():
            return
        self._refresh_theme_if_needed()
        image_path = self._render_image(title, items, top_index, selected_index, width_cells, height_cells)
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

    def _render_image(
        self,
        title: str,
        items: list[Zikr],
        top_index: int,
        selected_index: int,
        width_cells: int,
        height_cells: int,
    ) -> Path:
        content = "\n".join(f"{item.repeat}|{item.text}|{item.note}" for item in items)
        key = hashlib.sha256(
            f"{RENDER_VERSION}:{self._theme_signature}:{title}:{top_index}:{selected_index}:{width_cells}:{height_cells}:{content}".encode("utf-8")
        ).hexdigest()
        image_path = self.cache_dir / f"{key}.png"
        if image_path.exists():
            return image_path

        width_px = max(400, width_cells * 14)
        height_px = max(240, height_cells * 28)
        outer_margin_x = 20
        outer_margin_y = 18
        image = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        inner_left = outer_margin_x
        inner_top = outer_margin_y
        inner_right = width_px - outer_margin_x
        inner_bottom = height_px - outer_margin_y
        draw.rounded_rectangle(
            (inner_left, inner_top, inner_right, inner_bottom),
            radius=18,
            fill=(0, 0, 0, 0),
            outline=(245, 245, 245, 120),
            width=2,
        )

        draw.text((width_px // 2, outer_margin_y + 24), title, font=self.title_font, fill=self.theme.header, anchor="ma")
        y = outer_margin_y + 70
        right_x = inner_right - 36
        left_x = inner_left + 24
        available_width = max(320, inner_right - inner_left - 84)
        max_y = inner_bottom - 24

        for index in range(top_index, len(items)):
            item = items[index]
            selected = index == selected_index
            header_color = "#ffffff" if selected else self.theme.subheader
            text_color = "#ffffff" if selected else self.theme.text
            wrapped = self._wrap_arabic_text(draw, item.text, self.text_font, available_width)
            estimated_height = 30 + (len(wrapped) * 40) + (28 if item.note else 0) + 18
            if y + estimated_height > max_y:
                break

            draw.text((left_x, y), f"{index + 1}. {item.repeat}", font=self.ui_font, fill=header_color, anchor="la")
            y += 30
            for line in wrapped:
                if y + 40 > max_y:
                    break
                draw.text((right_x, y), line, font=self.text_font, fill=text_color, anchor="ra", direction="rtl", language="ar")
                y += 40
            if item.note:
                if y + 28 > max_y:
                    break
                draw.text((left_x + 18, y), item.note, font=self.ui_font_small, fill=self.theme.subheader, anchor="la")
                y += 28
            y += 18

        image.save(image_path)
        return image_path

    def _wrap_arabic_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        width_px: int,
    ) -> list[str]:
        words = text.split()
        if not words:
            return [text]
        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font, direction="rtl", language="ar")
            if bbox[2] - bbox[0] <= width_px:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

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
