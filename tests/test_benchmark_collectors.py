import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_settings import BenchmarkSettings, BASE_DIR
from collectors.factory import get_collector
from normalizers.factory import get_normalizer
from source_registry.loader import load_source_registry
from storage.benchmark_db import BenchmarkDatabase
from storage.benchmark_repository import BenchmarkRepository


class BenchmarkCollectorTests(unittest.TestCase):
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

    def test_collectors_store_raw_and_normalized_records(self):
        for source_name in ("kosis_household_finance_welfare_2024", "median_income_manual_2026"):
            source = self.registry.get(source_name)
            collector = get_collector(source.collector_key, self.settings)
            normalizer = get_normalizer(source.normalizer_key)
            collected = collector.collect(source, normalizer)
            self.repository.store_collected_source(source, collected)

        status_rows = self.repository.list_source_status()
        self.assertEqual(len(status_rows), 2)

        income_records = self.repository.get_normalized_records(
            source_name="kosis_household_finance_welfare_2024",
            metric_name="monthly_income",
        )
        self.assertTrue(income_records)
        self.assertEqual(income_records[0].metric_name, "monthly_income")

        median_records = self.repository.get_normalized_records(
            source_name="median_income_manual_2026",
            metric_name="median_income_by_household_size",
        )
        self.assertEqual(len(median_records), 5)


if __name__ == "__main__":
    unittest.main()
