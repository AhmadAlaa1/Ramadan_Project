# DuaTerm

> Prayer in your Terminal

DuaTerm is a terminal product for reading the Quran and Azkar with a calm TUI, offline bundled data, and a `kitty`-powered reading pane for reliable Arabic rendering.

```text
███╗   ██╗ ██████╗  ██████╗ ██████╗ ████████╗███████╗██████╗ ███╗   ███╗
████╗  ██║██╔═══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
██╔██╗ ██║██║   ██║██║   ██║██████╔╝   ██║   █████╗  ██████╔╝██╔████╔██║
██║╚██╗██║██║   ██║██║   ██║██╔══██╗   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
██║ ╚████║╚██████╔╝╚██████╔╝██║  ██║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
```

## Features

- Centered main menu with `Quran`, `Morning Azkar`, `Night Azkar`, and `Open Web UI`
- Offline Quran data bundled in the `quran-uthmani` edition
- `kitty` image rendering for cleaner Arabic reading
- Morning and Night Azkar views
- Browser fallback mode from inside the app
- Native packaging for Fedora/RPM, Debian/Ubuntu, and Arch

## Run

```bash
python3 main.py
```

If `kitty` is installed, DuaTerm relaunches itself there automatically for the best Arabic rendering.

You can also run:

```bash
./run-in-kitty.sh
```

Or install it locally:

```bash
python3 -m pip install -e .
duaterm
```

The legacy entrypoint still works too:

```bash
quran-tui
```

The previous `noorterm` entrypoint still works too.

## Packaging

Build the native package for the current distro with one command:

```bash
./build-package.sh
```

Supported targets:

- Fedora/RHEL: `.rpm`
- Ubuntu/Debian: `.deb`
- Arch: `.pkg.tar.zst`

## Build Dependencies

Fedora:

```bash
sudo dnf install rpm-build pyproject-rpm-macros python3-devel
```

Ubuntu/Debian:

```bash
sudo apt install debhelper dh-python pybuild-plugin-pyproject python3-all python3-pil python3-setuptools
```

Arch:

```bash
sudo pacman -S --needed base-devel python-build python-installer python-setuptools
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

## Notes

- The VS Code integrated terminal is not a reliable target for fully-correct Quranic Arabic rendering
- The app auto-prefers `kitty` because the reading pane is rendered as an image there
- Quran text and metadata are bundled locally, so runtime internet access is not required

## Philosophy

Technology should bring peace, not distraction.
