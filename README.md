# Quran Terminal Reader

Read the Holy Quran in the terminal with a split-pane TUI built on Python `curses`.

## Features

- Centered main menu with `Quran`, `Morning Azkar`, and `Night Azkar`.
- Browse all 114 surahs.
- Load Quran text from bundled offline data in the `quran-uthmani` edition.
- Scroll ayahs inside the terminal without external UI frameworks.
- Run fully offline after installation because the Quran data ships with the project.

## Requirements

- Python 3.11 or newer.
- A UTF-8 terminal with Arabic glyph support.

## Run

```bash
python3 main.py
```

The repository-local launcher also loads vendored Arabic rendering helpers from `vendor/` when present.

If you are using the VS Code integrated terminal, use `kitty` instead:

```bash
./run-in-kitty.sh
```

Or install it locally:

```bash
python3 -m pip install -e .
quran-tui
```

## RPM Packaging

Build a source tarball from the project root:

```bash
tar -czf quran-terminal-reader-0.1.0.tar.gz \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  --transform 's,^\.,quran-terminal-reader-0.1.0,' .
```

Then build the RPM:

```bash
rpmbuild -ta quran-terminal-reader-0.1.0.tar.gz
```

Or use the included spec directly:

```bash
rpmbuild -ba packaging/quran-terminal-reader.spec
```

Install with:

```bash
sudo dnf install ./noarch/quran-terminal-reader-0.1.0-1*.rpm
```

## Controls

- Main menu: `Up` / `Down` then `Enter`
- `Up` / `Down` or `j` / `k`: move in the focused panel
- `PageUp` / `PageDown`: scroll faster
- `Enter`: open the selected surah
- `Tab`: switch focus between surah list and ayah reader
- `s`: jump to a surah number
- `m`: cycle Arabic rendering mode: `bidi`, `plain`, `reshaped`
- `r`: reload bundled data from disk
- `Esc`: go back to the main menu
- `q`: quit from the main menu

## Arabic Rendering Modes

- `bidi`: reverses Arabic run order without forcing presentation-form glyphs. This is the default and usually works best in terminals that already shape Arabic but get RTL order wrong.
- `plain`: sends the original Quran text unchanged. Use this if your terminal already handles Arabic correctly.
- `reshaped`: forces Arabic shaping plus bidi reordering. Use this only for terminals that show Arabic letters disconnected and reversed.

You can set the startup mode with:

```bash
QURAN_TUI_ARABIC_MODE=bidi python3 main.py
```

The VS Code integrated terminal is not a reliable target for fully-correct Quranic Arabic rendering. For the most accurate result, run the app in `kitty`.

The UI uses an Arabic-first layout to avoid mixing English and Arabic on the same line, which reduces bidi rendering problems in terminal emulators.
When running inside `kitty`, the ayah pane is rendered as an image using `Noto Naskh Arabic`, which bypasses terminal bidi and shaping bugs.

## Notes

- Quran text and surah metadata are bundled in [data/surahs.json](/home/user/GitHub/Ramadan_Project/data/surahs.json) and [data/quran-uthmani.json](/home/user/GitHub/Ramadan_Project/data/quran-uthmani.json).
- The app no longer requires internet access at runtime.
