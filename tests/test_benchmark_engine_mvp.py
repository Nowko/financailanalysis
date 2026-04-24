import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_engine.service import build_default_benchmark_provider
from benchmark_settings import BASE_DIR, BenchmarkSettings
from collectors.factory import get_collector
from input_engine.validators import parse_household_input
from normalizers.factory import get_normalizer
from source_registry.loader import load_source_registry
from storage.benchmark_db import BenchmarkDatabase
from storage.benchmark_repository import BenchmarkRepository


class BenchmarkEngineMvpTests(unittest.TestCase):
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

        for source_name in ("kosis_household_finance_welfare_2024", "median_income_manual_2026"):
            source = self.registry.get(source_name)
            collector = get_collector(source.collector_key, self.settings)
            normalizer = get_normalizer(source.normalizer_key)
            collected = collector.collect(source, normalizer)
            self.repository.store_collected_source(source, collected)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_composite_provider_builds_household_benchmarks(self):
        sample_payload = json.loads(
            (BASE_DIR / "data/source_samples/sample_household_input.json").read_text(encoding="utf-8")
        )
        household_input = parse_household_input(sample_payload)
        provider = build_default_benchmark_provider(self.registry, self.repository)

        benchmark_context = provider.provide(household_input)

        self.assertIn("peer_monthly_income", benchmark_context.values)
        self.assertIn("peer_total_assets", benchmark_context.values)
        self.assertIn("median_income_reference", benchmark_context.values)
        self.assertEqual(benchmark_context.values["peer_monthly_income"].value, 720.0)
        self.assertEqual(benchmark_context.values["median_income_reference"].value, 670.0)


if __name__ == "__main__":
    unittest.main()
