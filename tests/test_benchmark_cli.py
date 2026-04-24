import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_settings import BASE_DIR, BenchmarkSettings
from source_registry.loader import load_source_registry
from storage.benchmark_db import BenchmarkDatabase
from storage.benchmark_repository import BenchmarkRepository
from ui import benchmark_cli


class BenchmarkCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = BenchmarkSettings(
            base_dir=BASE_DIR,
            db_path=Path(self.temp_dir.name) / "benchmark.sqlite3",
            registry_path=BASE_DIR / "data/source_registry/benchmark_sources.json",
            kosis_api_key="",
            kosis_use_mock=True,
        )
        self.registry = load_source_registry(self.settings.registry_path)
        self.repository = BenchmarkRepository(BenchmarkDatabase(self.settings.db_path))
        self.repository.initialize()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_update_and_demo_analysis_commands(self):
        sample_payload = json.loads(
            (BASE_DIR / "data/source_samples/sample_household_input.json").read_text(encoding="utf-8")
        )

        with patch.object(
            benchmark_cli,
            "_build_runtime",
            return_value=(self.settings, self.registry, self.repository),
        ), patch.object(
            benchmark_cli,
            "_load_household_payload",
            return_value=sample_payload,
        ), patch(
            "sys.stdout",
            new_callable=io.StringIO,
        ) as fake_stdout:
            benchmark_cli.cmd_update_sources(Namespace(only=None))
            benchmark_cli.cmd_demo_analysis(Namespace(input_file=None, print_json=False))

        output_text = fake_stdout.getvalue()
        self.assertIn("Updated kosis_household_finance_welfare_2024", output_text)
        self.assertIn("Updated median_income_manual_2026", output_text)
        self.assertTrue(self.repository.list_source_status())
        with self.repository.db.connect() as connection:
            snapshot_count = connection.execute(
                "SELECT COUNT(*) FROM analysis_snapshots"
            ).fetchone()[0]
        self.assertEqual(snapshot_count, 1)


if __name__ == "__main__":
    unittest.main()
