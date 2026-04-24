import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from output_logic.file_name_builder import (
    build_input_filename,
    build_report_filename,
    build_word_report_filename,
)


class FileNameBuilderTests(unittest.TestCase):
    def test_build_report_filename_prefers_birth_year_suffix(self):
        profile = SimpleNamespace(name="Hong Gil Dong", age=38, birth_year=1988)
        filename = build_report_filename(profile, today=date(2026, 4, 22))
        self.assertEqual(filename, "Hong_Gil_Dong_88.json")

    def test_build_report_filename_falls_back_when_name_missing(self):
        profile = SimpleNamespace(name="", age=45, birth_year=0)
        filename = build_report_filename(profile, today=date(2026, 4, 22))
        self.assertEqual(filename, "result_81.json")

    def test_build_input_filename_appends_input_suffix(self):
        payload = {"name": "Hong Gil Dong", "age": 38, "birth_year": 1988}
        filename = build_input_filename(payload, today=date(2026, 4, 22))
        self.assertEqual(filename, "Hong_Gil_Dong_88_입력.json")

    def test_build_input_filename_accepts_formatted_birth_year_string(self):
        payload = {"name": "Hong Gil Dong", "age": "38", "birth_year": "1,981"}
        filename = build_input_filename(payload, today=date(2026, 4, 22))
        self.assertEqual(filename, "Hong_Gil_Dong_81_입력.json")

    def test_build_word_report_filename_uses_birth_suffix_first(self):
        profile = SimpleNamespace(name="Hong Gil Dong", age=38, birth_year=1988)
        filename = build_word_report_filename(profile, today=date(2026, 4, 22))
        self.assertEqual(filename, "88_Hong_Gil_Dong.docx")


if __name__ == "__main__":
    unittest.main()
