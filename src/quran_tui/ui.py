from __future__ import annotations

import curses
import textwrap
from dataclasses import dataclass

from .api import QuranAPI, QuranAPIError
from .image_render import KittyAyahRenderer
from .model import SurahDetails, SurahSummary
from .rendering import (
    ARABIC_DISPLAY_MODES,
    DEFAULT_ARABIC_DISPLAY_MODE,
    prepare_terminal_text_with_mode,
)

PANEL_GAP = 1
MIN_SURAH_PANEL_WIDTH = 34


@dataclass
class ReaderState:
    surahs: list[SurahSummary]
    selected_surah_index: int = 0
    loaded_surah: SurahDetails | None = None
    ayah_top_line: int = 0
    surah_top_index: int = 0
    focus: str = "surahs"
    status: str = "Loading Quran data..."
    arabic_mode: str = DEFAULT_ARABIC_DISPLAY_MODE


class QuranReaderApp:
    def __init__(self, stdscr: curses.window, api: QuranAPI) -> None:
        self.stdscr = stdscr
        self.api = api
        self.state = ReaderState(surahs=[])
        self.kitty_renderer = KittyAyahRenderer()
        self.needs_redraw = True

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.keypad(True)
        curses.use_default_colors()
        self.stdscr.timeout(-1)
        self._init_colors()
        self._bootstrap()

        while True:
            if self.needs_redraw:
                self._draw()
                self.needs_redraw = False
            key = self.stdscr.getch()
            if not self._handle_key(key):
                self.kitty_renderer.clear()
                break

    def _bootstrap(self) -> None:
        try:
            self.state.surahs = self.api.list_surahs()
            self._load_surah(self.state.selected_surah_index)
        except QuranAPIError as exc:
            self.state.status = f"Load failed: {exc}"

    def _init_colors(self) -> None:
        if not curses.has_colors():
            return
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)

    def _handle_key(self, key: int) -> bool:
        if key in (ord("q"), 27):
            return False
        if key in (9, ord("\t")):
            self.state.focus = "ayahs" if self.state.focus == "surahs" else "surahs"
            self.needs_redraw = True
            return True
        if key in (ord("r"), ord("R")):
            self._refresh_current_surah()
            self.needs_redraw = True
            return True
        if key in (ord("s"), ord("S")):
            self._prompt_surah_number()
            self.needs_redraw = True
            return True
        if key in (ord("m"), ord("M")):
            self._cycle_arabic_mode()
            self.needs_redraw = True
            return True
        if key == curses.KEY_RESIZE:
            self.kitty_renderer.last_image = None
            self.kitty_renderer.last_place = None
            self.needs_redraw = True
            return True

        if self.state.focus == "surahs":
            handled = self._handle_surah_keys(key)
        else:
            handled = self._handle_ayah_keys(key)
        self.needs_redraw = True
        return handled

    def _handle_surah_keys(self, key: int) -> bool:
        if not self.state.surahs:
            return True
        previous_index = self.state.selected_surah_index

        if key in (curses.KEY_UP, ord("k")):
            self.state.selected_surah_index = max(0, self.state.selected_surah_index - 1)
            self._ensure_surah_visible()
        elif key in (curses.KEY_DOWN, ord("j")):
            self.state.selected_surah_index = min(
                len(self.state.surahs) - 1,
                self.state.selected_surah_index + 1,
            )
            self._ensure_surah_visible()
        elif key in (curses.KEY_NPAGE,):
            self.state.selected_surah_index = min(
                len(self.state.surahs) - 1,
                self.state.selected_surah_index + 10,
            )
            self._ensure_surah_visible()
        elif key in (curses.KEY_PPAGE,):
            self.state.selected_surah_index = max(0, self.state.selected_surah_index - 10)
            self._ensure_surah_visible()
        elif key in (curses.KEY_HOME, ord("g")):
            self.state.selected_surah_index = 0
            self._ensure_surah_visible()
        elif key in (curses.KEY_END, ord("G")):
            self.state.selected_surah_index = len(self.state.surahs) - 1
            self._ensure_surah_visible()
        elif key in (10, 13, curses.KEY_ENTER, curses.KEY_RIGHT, ord("l")):
            self._load_surah(self.state.selected_surah_index)
            self.state.focus = "ayahs"
            return True

        if self.state.selected_surah_index != previous_index:
            self._load_surah(self.state.selected_surah_index)
        return True

    def _handle_ayah_keys(self, key: int) -> bool:
        if self.state.loaded_surah is None:
            return True

        if self.kitty_renderer.is_supported():
            total_lines = self.kitty_renderer.get_total_lines(self.state.loaded_surah, self._ayah_panel_width())
            visible_height = max(1, self._content_height())
        else:
            total_lines = len(self._build_ayah_lines(self._ayah_width()))
            visible_height = self._content_height()
        max_top = max(0, total_lines - visible_height)

        if key in (curses.KEY_UP, ord("k")):
            self.state.ayah_top_line = max(0, self.state.ayah_top_line - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.state.ayah_top_line = min(max_top, self.state.ayah_top_line + 1)
        elif key == curses.KEY_NPAGE:
            self.state.ayah_top_line = min(max_top, self.state.ayah_top_line + visible_height)
        elif key == curses.KEY_PPAGE:
            self.state.ayah_top_line = max(0, self.state.ayah_top_line - visible_height)
        elif key in (curses.KEY_HOME, ord("g")):
            self.state.ayah_top_line = 0
        elif key in (curses.KEY_END, ord("G")):
            self.state.ayah_top_line = max_top
        elif key in (curses.KEY_LEFT, ord("h")):
            self.state.focus = "surahs"
        return True

    def _load_surah(self, surah_index: int, refresh: bool = False) -> None:
        if not self.state.surahs:
            return

        surah = self.state.surahs[surah_index]
        try:
            self.state.loaded_surah = self.api.get_surah(surah.number, refresh=refresh)
            self.state.ayah_top_line = 0
            self.state.status = (
                f"Loaded {surah.number}. {surah.english_name} "
                f"({surah.number_of_ayahs} ayahs, {surah.revelation_type})."
            )
            self.kitty_renderer.last_image = None
            self.kitty_renderer.last_place = None
        except QuranAPIError as exc:
            self.state.status = f"Failed to load surah {surah.number}: {exc}"

    def _refresh_current_surah(self) -> None:
        try:
            self.state.surahs = self.api.list_surahs(refresh=True)
            self._load_surah(self.state.selected_surah_index, refresh=True)
            self.state.status = f"Refreshed from API. Arabic mode: {self.state.arabic_mode}."
        except QuranAPIError as exc:
            self.state.status = f"Refresh failed: {exc}"

    def _cycle_arabic_mode(self) -> None:
        modes = sorted(ARABIC_DISPLAY_MODES, key=lambda item: ("bidi", "plain", "reshaped").index(item))
        current_index = modes.index(self.state.arabic_mode)
        self.state.arabic_mode = modes[(current_index + 1) % len(modes)]
        self.state.status = (
            "Arabic rendering mode changed to "
            f"{self.state.arabic_mode}. Press m again to cycle."
        )

    def _prompt_surah_number(self) -> None:
        height, width = self.stdscr.getmaxyx()
        prompt = "Go to surah number (1-114): "
        input_width = min(max(len(prompt) + 6, 32), max(20, width - 4))
        x = max(0, (width - input_width) // 2)
        y = max(1, height // 2)
        window = curses.newwin(3, input_width, y, x)
        window.keypad(True)
        window.border()
        curses.curs_set(1)
        buffer = ""

        while True:
            window.erase()
            window.border()
            window.addnstr(1, 1, prompt + buffer, input_width - 2)
            window.refresh()
            key = window.getch()

            if key in (27,):
                self.state.status = "Jump cancelled."
                break
            if key in (10, 13, curses.KEY_ENTER):
                if self._apply_surah_jump(buffer):
                    break
                continue
            if key in (curses.KEY_BACKSPACE, 127, 8):
                buffer = buffer[:-1]
                continue
            if 48 <= key <= 57 and len(buffer) < 3:
                buffer += chr(key)

        curses.curs_set(0)
        del window
        self.needs_redraw = True

    def _apply_surah_jump(self, raw_value: str) -> bool:
        if not raw_value:
            self.state.status = "Enter a surah number between 1 and 114."
            return False

        number = int(raw_value)
        if number < 1 or number > len(self.state.surahs):
            self.state.status = "Surah number out of range."
            return False

        self.state.selected_surah_index = number - 1
        self._ensure_surah_visible()
        self._load_surah(self.state.selected_surah_index)
        self.state.focus = "ayahs"
        self.needs_redraw = True
        return True

    def _ensure_surah_visible(self) -> None:
        visible = self._content_height()
        index = self.state.selected_surah_index
        if index < self.state.surah_top_index:
            self.state.surah_top_index = index
        elif index >= self.state.surah_top_index + visible:
            self.state.surah_top_index = index - visible + 1

    def _draw(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 10 or width < 60:
            self._safe_addnstr(0, 0, "Resize terminal to at least 60x10.", width - 1)
            self.stdscr.refresh()
            return

        surah_width = max(MIN_SURAH_PANEL_WIDTH, min(42, width // 3))
        ayah_x = surah_width + PANEL_GAP
        ayah_width = width - ayah_x

        self._draw_surah_panel(0, 0, height - 1, surah_width)
        self._draw_ayah_panel(0, ayah_x, height - 1, ayah_width)
        self._draw_status_bar(height - 1, width)
        self.stdscr.refresh()

    def _draw_surah_panel(self, y: int, x: int, height: int, width: int) -> None:
        self._draw_box(y, x, height, width, "Surahs")
        inner_width = width - 2
        top = self.state.surah_top_index
        bottom = min(len(self.state.surahs), top + height - 2)

        for row, index in enumerate(range(top, bottom), start=1):
            surah = self.state.surahs[index]
            attr = curses.A_NORMAL
            if index == self.state.selected_surah_index:
                attr = curses.color_pair(2) if curses.has_colors() else curses.A_REVERSE
            elif surah.revelation_type.lower() == "meccan":
                attr = curses.color_pair(1) if curses.has_colors() else curses.A_NORMAL

            number_label = f"{surah.number:>3}."
            english_label = surah.english_name
            arabic_label = self._render_arabic(surah.arabic_name) if surah.arabic_name else ""
            english_width = min(len(english_label), max(0, inner_width // 2))
            self._safe_addnstr(y + row, x + 1, number_label, len(number_label), attr)
            self._safe_addnstr(y + row, x + 6, english_label, english_width, attr)
            if arabic_label:
                arabic_width = min(len(arabic_label), max(0, inner_width - 6 - english_width - 1))
                arabic_x = x + width - 1 - arabic_width
                self._safe_addnstr(y + row, arabic_x, arabic_label, arabic_width, attr)

    def _draw_ayah_panel(self, y: int, x: int, height: int, width: int) -> None:
        title = "Ayahs"
        if self.state.loaded_surah is not None:
            summary = self.state.loaded_surah.summary
            title = f"{summary.number}. {self._render_arabic(summary.arabic_name)}"
        self._draw_box(y, x, height, width, title)

        if self.state.loaded_surah is None:
            self._safe_addnstr(y + 1, x + 1, "No surah loaded.", width - 2)
            return

        if self.kitty_renderer.is_supported():
            self.kitty_renderer.draw(
                self.state.loaded_surah,
                self.state.ayah_top_line,
                max(10, width - 2),
                max(4, height - 2),
                x + 1,
                y + 1,
            )
            return

        lines = self._build_ayah_lines(width - 2)
        visible = lines[self.state.ayah_top_line : self.state.ayah_top_line + height - 2]
        for row, (gutter, text) in enumerate(visible, start=1):
            if gutter:
                gutter_attr = curses.color_pair(3) if curses.has_colors() else curses.A_BOLD
                self._safe_addnstr(y + row, x + 1, gutter, 6, gutter_attr)
            rendered_text = self._render_arabic(text)
            available_width = max(1, width - 8)
            text_width = min(len(rendered_text), available_width)
            text_x = x + width - 1 - text_width
            self._safe_addnstr(y + row, text_x, rendered_text, text_width)

    def _draw_status_bar(self, y: int, width: int) -> None:
        focus_text = "Surahs" if self.state.focus == "surahs" else "Ayahs"
        help_text = f"Tab switch | Enter open | s jump | m mode:{self.state.arabic_mode} | r refresh | q quit"
        status = f"{self.state.status}  [{focus_text}]  {help_text}"
        attr = curses.color_pair(2) if curses.has_colors() else curses.A_REVERSE
        self._safe_addnstr(y, 0, status.ljust(max(1, width - 1)), max(1, width - 1), attr)

    def _draw_box(self, y: int, x: int, height: int, width: int, title: str) -> None:
        self.stdscr.addch(y, x, curses.ACS_ULCORNER)
        self.stdscr.hline(y, x + 1, curses.ACS_HLINE, width - 2)
        self.stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
        self.stdscr.vline(y + 1, x, curses.ACS_VLINE, height - 2)
        self.stdscr.vline(y + 1, x + width - 1, curses.ACS_VLINE, height - 2)
        self.stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
        self.stdscr.hline(y + height - 1, x + 1, curses.ACS_HLINE, width - 2)
        self.stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
        if title:
            self._safe_addnstr(y, x + 2, f" {title} ", width - 4)

    def _content_height(self) -> int:
        return max(1, self.stdscr.getmaxyx()[0] - 3)

    def _ayah_width(self) -> int:
        width = self.stdscr.getmaxyx()[1]
        surah_width = max(MIN_SURAH_PANEL_WIDTH, min(42, width // 3))
        ayah_x = surah_width + PANEL_GAP
        return max(20, width - ayah_x - 8)

    def _ayah_panel_width(self) -> int:
        width = self.stdscr.getmaxyx()[1]
        surah_width = max(MIN_SURAH_PANEL_WIDTH, min(42, width // 3))
        ayah_x = surah_width + PANEL_GAP
        return max(10, width - ayah_x - 2)

    def _build_ayah_lines(self, width: int) -> list[tuple[str, str]]:
        if self.state.loaded_surah is None:
            return []

        lines: list[tuple[str, str]] = []
        wrap_width = max(10, width)
        for ayah in self.state.loaded_surah.ayahs:
            wrapped = textwrap.wrap(
                ayah.text,
                width=wrap_width,
                break_long_words=False,
                replace_whitespace=False,
                drop_whitespace=False,
            ) or [ayah.text]
            gutter = f"{ayah.number_in_surah:>4} "
            for index, line in enumerate(wrapped):
                lines.append((gutter if index == 0 else "", line))
        return lines

    def _safe_addnstr(self, y: int, x: int, text: str, max_chars: int, attr: int = 0) -> None:
        height, width = self.stdscr.getmaxyx()
        if y < 0 or x < 0 or y >= height or x >= width or max_chars <= 0:
            return

        available = min(max_chars, width - x)
        if available <= 0:
            return

        # Avoid drawing into the terminal's bottom-right cell, which often raises ERR.
        if y == height - 1:
            available = min(available, width - x - 1)
        if available <= 0:
            return

        try:
            self.stdscr.addnstr(y, x, text, available, attr)
        except curses.error:
            pass

    def _render_arabic(self, text: str) -> str:
        return prepare_terminal_text_with_mode(text, self.state.arabic_mode)


def run_app(api: QuranAPI) -> None:
    curses.wrapper(lambda stdscr: QuranReaderApp(stdscr, api).run())
