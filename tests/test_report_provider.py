import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import REPORT_BENCHMARK_FILE
from calc_logic.providers.report_provider import ReportBenchmarkProvider


class ReportProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = ReportBenchmarkProvider(REPORT_BENCHMARK_FILE)

    def _profile(self, income: float):
        return SimpleNamespace(
            age=25,
            marital_status="single",
            children_count=0,
            youngest_child_stage="none",
            household_income=income,
        )

    def test_cutoff_band_selection_uses_report_ranges(self):
        low_selection = self.provider.select_group_and_band(self._profile(279.9))
        mid_selection = self.provider.select_group_and_band(self._profile(280))
        high_selection = self.provider.select_group_and_band(self._profile(750))

        self.assertEqual(low_selection["band_key"], "1")
        self.assertEqual(mid_selection["band_key"], "2")
        self.assertEqual(high_selection["band_key"], "5")
        self.assertEqual(mid_selection["selection_method"], "cutoff")

    def test_midpoint_fallback_still_works_without_cutoff_rules(self):
        bands = {
            "1": {"household_income": 100},
            "2": {"household_income": 200},
            "3": {"household_income": 400},
        }
        band_key, band_rule, selection_method = self.provider._select_income_band(bands, 260, {})
        self.assertEqual(band_key, "2")
        self.assertEqual(selection_method, "derived_midpoint")
        self.assertEqual(band_rule["min"], 150.0)
        self.assertEqual(band_rule["max"], 300.0)

    def test_tax_benefit_rules_are_loaded_from_json(self):
        payload = self.provider.get_tax_benefit_rules()

        self.assertEqual(payload["method"], "external_tax_rule_lookup")
        self.assertEqual(payload["tax_source"], "국세청 2026")
        self.assertIn("pension_savings", payload["products"])
        self.assertEqual(payload["products"]["housing_subscription"]["benefit_type"], "income_deduction")


if __name__ == "__main__":
    unittest.main()
