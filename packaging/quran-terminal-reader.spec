Name:           quran-terminal-reader
Version:        0.1.0
Release:        1%{?dist}
Summary:        Terminal TUI for reading the Quran and Azkar

License:        MIT
URL:            https://example.invalid/quran-terminal-reader
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

Requires:       kitty

%description
Quran Terminal Reader is an offline terminal application for reading the Quran
and Azkar with a curses interface and kitty image rendering for high-quality
Arabic text display.

%prep
%autosetup -n %{name}-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files quran_tui

%check
python3 -m unittest discover -s tests -v

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/quran-tui

%changelog
* Wed Mar 18 2026 Codex <codex@example.invalid> - 0.1.0-1
- Initial RPM package
