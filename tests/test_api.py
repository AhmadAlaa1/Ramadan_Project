from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quran_tui.api import QuranAPI, QuranAPIError


SURAH_LIST_PAYLOAD = {
    "status": "OK",
    "data": [
        {
            "number": 1,
            "name": "الفاتحة",
            "englishName": "Al-Faatiha",
            "englishNameTranslation": "The Opening",
            "numberOfAyahs": 7,
            "revelationType": "Meccan",
        }
    ],
}

QURAN_PAYLOAD = {
    "status": "OK",
    "data": {
        "edition": {"identifier": "quran-uthmani"},
        "surahs": [
            {
                "number": 1,
                "name": "الفاتحة",
                "englishName": "Al-Faatiha",
                "englishNameTranslation": "The Opening",
                "numberOfAyahs": 7,
                "revelationType": "Meccan",
                "ayahs": [
                    {"numberInSurah": 1, "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"},
                    {"numberInSurah": 2, "text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"},
                ],
            }
        ],
    },
}


class QuranAPITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_dir = Path(self.temp_dir.name)
        (self.data_dir / "surahs.json").write_text(
            json.dumps(SURAH_LIST_PAYLOAD, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.data_dir / "quran-uthmani.json").write_text(
            json.dumps(QURAN_PAYLOAD, ensure_ascii=False),
            encoding="utf-8",
        )
        self.api = QuranAPI(data_dir=self.data_dir)

    def test_list_surahs_parses_bundled_data(self) -> None:
        surahs = self.api.list_surahs()
        self.assertEqual(len(surahs), 1)
        self.assertEqual(surahs[0].arabic_name, "الفاتحة")
        self.assertEqual(surahs[0].number_of_ayahs, 7)

    def test_get_surah_reads_bundled_quran_text(self) -> None:
        surah = self.api.get_surah(1)
        self.assertEqual(surah.summary.english_name, "Al-Faatiha")
        self.assertEqual(len(surah.ayahs), 2)
        self.assertEqual(surah.ayahs[0].text, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")

    def test_missing_bundled_file_raises_clear_error(self) -> None:
        (self.data_dir / "quran-uthmani.json").unlink()
        api = QuranAPI(data_dir=self.data_dir)
        with self.assertRaises(QuranAPIError):
            api.get_surah(1, refresh=True)


if __name__ == "__main__":
    unittest.main()
