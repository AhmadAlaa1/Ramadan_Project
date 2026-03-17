from __future__ import annotations

from .api import QuranAPI
from .ui import run_app


def main() -> None:
    run_app(QuranAPI())


if __name__ == "__main__":
    main()
