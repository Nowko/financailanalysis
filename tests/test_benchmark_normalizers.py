import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from normalizers.document_source_normalizer import DocumentSourceNormalizer
from normalizers.kosis_household_normalizer import KosisHouseholdSurveyNormalizer
from normalizers.median_income_normalizer import MedianIncomeNormalizer
from source_registry.loader import load_source_registry


class BenchmarkNormalizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_source_registry(
            Path(__file__).resolve().parents[1] / "data/source_registry/benchmark_sources.json"
        )

    def test_kosis_normalizer_maps_household_metrics(self):
        source = self.registry.get("kosis_household_finance_welfare_2024")
        payload = {
            "dataset_key": "sample",
            "period_year": 2024,
            "unit": "만원",
            "rows": [
                {
                    "household_size": 4,
                    "age_band": "40s",
                    "monthly_income": 700,
                    "disposable_income": 560,
                    "total_assets": 80000,
                    "financial_assets": 18000,
                    "real_estate_assets": 56000,
                    "total_debt": 12000,
                    "monthly_consumption": 390,
                }
            ],
        }

        records = KosisHouseholdSurveyNormalizer().normalize(payload, source)

        self.assertEqual(len(records), 7)
        self.assertEqual(records[0].household_size, 4)
        self.assertEqual(records[0].age_band, "40s")

    def test_median_income_normalizer_creates_household_size_records(self):
        source = self.registry.get("median_income_manual_2026")
        payload = {
            "dataset_key": "manual",
            "period_year": 2026,
            "unit": "만원",
            "rows": [
                {"household_size": 3, "median_income_by_household_size": 553},
            ],
        }

        records = MedianIncomeNormalizer().normalize(payload, source)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].metric_name, "median_income_by_household_size")
        self.assertEqual(records[0].household_size, 3)

    def test_document_normalizer_keeps_auxiliary_fields(self):
        source = self.registry.get("document_wealth_report_sample_2024")
        payload = {
            "dataset_key": "doc",
            "period_year": 2024,
            "rows": [
                {
                    "metric_name": "wealth_report_total_assets_reference",
                    "value": 100000,
                    "unit": "만원",
                    "segment": "affluent_household",
                    "age_band": "40s",
                }
            ],
        }

        records = DocumentSourceNormalizer().normalize(payload, source)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].attributes["segment"], "affluent_household")


if __name__ == "__main__":
    unittest.main()
