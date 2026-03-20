Name:           noorterm
Version:        0.1.0
Release:        1%{?dist}
Summary:        Offline Quran reading and Azkar with bundled data

License:        MIT
URL:            https://example.invalid/noorterm
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

Requires:       kitty
Requires:       google-noto-naskh-arabic-fonts
Requires:       google-noto-sans-fonts

%description
NoorTerm provides offline Quran reading and Azkar with bundled
data, keyboard navigation, and kitty-powered Arabic rendering.
It includes morning and night Azkar, the 99 Names of Allah, and a
web UI fallback.

%prep
%autosetup -n %{name}-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files noorterm

%check
python3 -m unittest discover -s tests -v

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/noorterm

%changelog
* Wed Mar 18 2026 NoorTerm Maintainers <maintainers@noorterm.invalid> - 0.1.0-1
- Initial RPM package
