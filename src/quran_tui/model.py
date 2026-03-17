from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SurahSummary:
    number: int
    arabic_name: str
    english_name: str
    english_translation: str
    number_of_ayahs: int
    revelation_type: str


@dataclass(frozen=True)
class Ayah:
    number_in_surah: int
    text: str


@dataclass(frozen=True)
class SurahDetails:
    summary: SurahSummary
    ayahs: list[Ayah]
