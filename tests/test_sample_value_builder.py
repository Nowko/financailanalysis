import sys
import unittest
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.providers.report_provider import ReportBenchmarkProvider
from calc_logic.sample_value_builder import build_reference_sample_values
from config import REPORT_BENCHMARK_FILE


class SampleValueBuilderTests(unittest.TestCase):
    def test_reference_sample_uses_report_categories_and_balanced_products(self):
        provider = ReportBenchmarkProvider(REPORT_BENCHMARK_FILE)
        profile_like = SimpleNamespace(
            age=45,
            marital_status="married",
            children_count=1,
            youngest_child_stage="middle_high",
            household_income=628,
            monthly_saving_investment=108,
        )

        sample = build_reference_sample_values(provider, profile_like)
        selection = provider.select_group_and_band(profile_like)

        self.assertEqual(
            sample["expense_categories"]["food"],
            float(selection["band"]["expense_categories"]["food"]),
        )
        self.assertEqual(sample["saving_products"]["pension_savings"], 50.0)
        self.assertEqual(sample["saving_products"]["irp"], 25.0)
        self.assertEqual(sample["saving_products"]["housing_subscription"], 25.0)
        self.assertAlmostEqual(
            sum(sample["saving_products"].values()) + sum(sample["insurance_products"].values()),
            sample["financial_fields"]["monthly_saving_investment"],
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
