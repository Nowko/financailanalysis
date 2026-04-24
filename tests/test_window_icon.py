import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.window_icon import resolve_icon_path


class WindowIconTests(unittest.TestCase):
    def test_resolve_icon_path_returns_first_existing_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing = temp_path / "missing.ico"
            existing = temp_path / "Financial-analisys.ico"
            existing.write_bytes(b"ico")

            resolved = resolve_icon_path((missing, existing))

            self.assertEqual(resolved, existing)

    def test_resolve_icon_path_returns_none_when_no_candidate_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resolved = resolve_icon_path((temp_path / "missing1.ico", temp_path / "missing2.ico"))
            self.assertIsNone(resolved)


if __name__ == "__main__":
    unittest.main()
