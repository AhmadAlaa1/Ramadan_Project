# NoorTerm

> Prayer in your Terminal

NoorTerm is a terminal product for reading the Quran and Azkar with a calm TUI, offline bundled data, and a `kitty`-powered reading pane for reliable Arabic rendering.

```text
███╗   ██╗ ██████╗  ██████╗ ██████╗ ████████╗███████╗██████╗ ███╗   ███╗
████╗  ██║██╔═══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
██╔██╗ ██║██║   ██║██║   ██║██████╔╝   ██║   █████╗  ██████╔╝██╔████╔██║
██║╚██╗██║██║   ██║██║   ██║██╔══██╗   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
██║ ╚████║╚██████╔╝╚██████╔╝██║  ██║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
```



https://github.com/user-attachments/assets/7f5c9886-3830-4701-a3d2-ccc4a3131b16



## Features

- Centered main menu with `Quran`, `Morning Azkar`, `Night Azkar`, and `Open Web UI`
- Offline Quran data bundled in the `quran-uthmani` edition
- `kitty` image rendering for cleaner Arabic reading
- Morning and Night Azkar views
- Browser fallback mode from inside the app
- Native packaging for Fedora/RPM, Debian/Ubuntu, and Arch(Coming Soon!)

## WebUi

https://github.com/user-attachments/assets/2deac8fc-84e9-4ba5-94fe-088f735bea47

## The official Website

- https://ahmadalaa1.github.io/NoorTerm/

GitHub repo:

- [Main Repo](https://github.com/AhmadAlaa1/NoorTerm)
- [Download Latest Release](https://github.com/AhmadAlaa1/NoorTerm/releases)

Install command:

```bash
curl -fsSL https://raw.githubusercontent.com/AhmadAlaa1/noorterm/main/install.sh | NOORTERM_GITHUB_REPO=AhmadAlaa1/noorterm bash
```

The installer auto-detects:

- Debian/Ubuntu: installs the latest `.deb`
- Fedora/RHEL: installs the latest `.rpm`

## Build it by yourself

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
