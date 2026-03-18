from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import Ayah, SurahDetails, SurahSummary


class QuranAPIError(RuntimeError):
    """Raised when the bundled Quran data cannot be loaded or parsed."""


class QuranAPI:
    def __init__(self, data_dir: Path | None = None) -> None:
        package_dir = Path(__file__).resolve().parent
        self.data_dir = data_dir or (package_dir / "data")
        self._surah_list_payload: list[dict[str, Any]] | None = None
        self._surah_summary_map: dict[int, dict[str, Any]] | None = None
        self._surah_map_payload: dict[int, dict[str, Any]] | None = None

    def list_surahs(self, refresh: bool = False) -> list[SurahSummary]:
        if refresh or self._surah_list_payload is None:
            payload = self._read_json(self.data_dir / "surahs.json")
            data = payload.get("data")
            if not isinstance(data, list):
                raise QuranAPIError("Bundled surah metadata is invalid.")
            self._surah_list_payload = data
            self._surah_summary_map = {
                item["number"]: item for item in data if isinstance(item, dict) and "number" in item
            }
        return [self._parse_surah_summary(item) for item in self._surah_list_payload]

    def get_surah(self, number: int, refresh: bool = False) -> SurahDetails:
        surah_map = self._load_surah_map(refresh=refresh)
        summary_map = self._load_summary_map(refresh=refresh)
        payload = surah_map.get(number)
        if payload is None:
            raise QuranAPIError(f"Bundled surah {number} was not found.")
        summary_payload = summary_map.get(number)
        if summary_payload is None:
            raise QuranAPIError(f"Bundled metadata for surah {number} was not found.")

        summary = self._parse_surah_summary(summary_payload)
        ayahs_raw = payload.get("ayahs")
        if not isinstance(ayahs_raw, list):
            raise QuranAPIError(f"Bundled surah {number} has invalid ayah data.")

        ayahs = [
            Ayah(number_in_surah=item["numberInSurah"], text=item["text"])
            for item in ayahs_raw
        ]
        return SurahDetails(summary=summary, ayahs=ayahs)

    def _load_summary_map(self, refresh: bool) -> dict[int, dict[str, Any]]:
        if refresh or self._surah_summary_map is None:
            self.list_surahs(refresh=refresh)
        return self._surah_summary_map or {}

    def _load_surah_map(self, refresh: bool) -> dict[int, dict[str, Any]]:
        if refresh or self._surah_map_payload is None:
            payload = self._read_json(self.data_dir / "quran-uthmani.json")
            data = payload.get("data", {})
            surahs = data.get("surahs")
            if not isinstance(surahs, list):
                raise QuranAPIError("Bundled Quran text is invalid.")
            self._surah_map_payload = {
                item["number"]: item for item in surahs if isinstance(item, dict) and "number" in item
            }
        return self._surah_map_payload

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise QuranAPIError(f"Bundled data file is missing: {path.name}") from exc
        except json.JSONDecodeError as exc:
            raise QuranAPIError(f"Bundled data file is invalid JSON: {path.name}") from exc
        except OSError as exc:
            raise QuranAPIError(f"Bundled data file could not be read: {path.name}") from exc

    def _parse_surah_summary(self, item: dict[str, Any]) -> SurahSummary:
        return SurahSummary(
            number=item["number"],
            arabic_name=item["name"],
            english_name=item["englishName"],
            english_translation=item["englishNameTranslation"],
            number_of_ayahs=item["numberOfAyahs"],
            revelation_type=item["revelationType"],
        )
