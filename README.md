<div align="center">

<pre>
███╗   ██╗ ██████╗  ██████╗ ██████╗ ████████╗███████╗██████╗ ███╗   ███╗
████╗  ██║██╔═══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
██╔██╗ ██║██║   ██║██║   ██║██████╔╝   ██║   █████╗  ██████╔╝██╔████╔██║
██║╚██╗██║██║   ██║██║   ██║██╔══██╗   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
██║ ╚████║╚██████╔╝╚██████╔╝██║  ██║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
</pre>

> Prayer in your Terminal

A calm terminal application for reading the Quran and daily Azkar,  
with offline bundled data and a `kitty`-powered reading pane for reliable Arabic rendering.

<br>

![Profile Views](https://komarev.com/ghpvc/?username=AhmadAlaa1&color=orange)
![Stars](https://img.shields.io/github/stars/AhmadAlaa1/NoorTerm?style=social)
![Watchers](https://img.shields.io/github/watchers/AhmadAlaa1/NoorTerm?style=social)
![Downloads](https://img.shields.io/github/downloads/AhmadAlaa1/NoorTerm/total)
![Release](https://img.shields.io/github/v/release/AhmadAlaa1/NoorTerm)

</div>

---

## 🎬 Demo

https://github.com/user-attachments/assets/2deac8fc-84e9-4ba5-94fe-088f735bea47

---

## ✨ Features

- 🧭 Centered main menu with:
  - Quran
  - Morning Azkar
  - Night Azkar
  - Open Web UI
- 📦 Fully offline Quran data (`quran-uthmani`)
- 🖼️ `kitty` image rendering for clean Arabic display
- 🌅 Morning & 🌙 Night Azkar views
- 🌐 Built-in browser fallback mode
- 📦 Native packaging:
  - Fedora / RHEL → `.rpm`
  - Debian / Ubuntu → `.deb`
  - Arch Linux → *(coming soon)*

---

## 🌐 Web UI

https://github.com/user-attachments/assets/7f5c9886-3830-4701-a3d2-ccc4a3131b16

---

## 🔗 Links

- 🌍 Website:  
  https://ahmadalaa1.github.io/NoorTerm/

- 📦 Main Repository:  
  https://github.com/AhmadAlaa1/NoorTerm

- ⬇️ Download Latest Release:  
  https://github.com/AhmadAlaa1/NoorTerm/releases

---

## ⚡ Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/AhmadAlaa1/noorterm/main/install.sh | NOORTERM_GITHUB_REPO=AhmadAlaa1/noorterm bash
```
The installer auto-detects:
- Debian / Ubuntu → installs .deb
- Fedora / RHEL → installs .rpm

---

## 🛠️ Build from Source
```bash
./build-package.sh
```
Supported targets:
- Fedora / RHEL → .rpm
- Debian / Ubuntu → .deb
- Arch Linux → .pkg.tar.zst

---

## 📦 Build Dependencies

**Fedora**:
```bash
sudo dnf install rpm-build pyproject-rpm-macros python3-devel
```
**Ubuntu/Debian**:
```bash
sudo apt install debhelper dh-python pybuild-plugin-pyproject python3-all python3-pil python3-setuptools
```
**Arch**:
```bash
sudo pacman -S --needed base-devel python-build python-installer python-setuptools
```
---

## 🎮 Controls

- ```↑ / ↓``` → navigate menu
- ```Enter``` → select option
- ```j / k``` → move in panel
- ```PageUp / PageDown``` → fast scroll
- ```Tab``` → switch panels
- ```s``` → jump to surah
- ```m``` → switch rendering mode (bidi, plain, reshaped)
- ```r``` → reload data
- ```Esc``` → back to menu
- ```q``` → quit
