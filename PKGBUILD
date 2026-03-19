pkgname=duaterm
pkgver=0.1.0
pkgrel=1
pkgdesc="Terminal TUI for reading the Quran and Azkar offline"
arch=('any')
url="https://example.invalid/duaterm"
license=('MIT')
depends=(
  'python'
  'python-pillow'
  'kitty'
  'noto-fonts'
)
makedepends=(
  'python-build'
  'python-installer'
  'python-setuptools'
)
source=("${pkgname}-${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
  cd "${srcdir}/${pkgname}-${pkgver}"
  python -m build --wheel --no-isolation
}

package() {
  cd "${srcdir}/${pkgname}-${pkgver}"
  python -m installer --destdir="${pkgdir}" dist/*.whl

  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
  install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
  install -Dm755 run-in-kitty.sh "${pkgdir}/usr/share/${pkgname}/run-in-kitty.sh"
}
