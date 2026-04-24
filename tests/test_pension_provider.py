import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DEFAULT_PENSION_ASSUMPTIONS
from calc_logic.providers.pension_provider import PensionBenchmarkProvider
from models.client_profile import PensionProfile


class PensionProviderTests(unittest.TestCase):
    def test_retirement_age_is_adjusted_when_not_in_future(self):
        provider = PensionBenchmarkProvider(DEFAULT_PENSION_ASSUMPTIONS)
        pension_profile = PensionProfile(
            current_age=45,
            retirement_age=45,
            expected_monthly_pension=200,
            current_balance=3000,
        )

        result = provider.calculate_required_monthly_contribution(pension_profile)

        self.assertEqual(result["detail"]["applied_retirement_age"], 46)
        self.assertTrue(result["detail"]["retirement_age_adjusted"])
        self.assertEqual(result["months_to_retirement"], 12)
        self.assertGreaterEqual(result["required_monthly_contribution"], 0)
        self.assertGreater(
            result["inflation_adjusted_monthly_pension_at_retirement"],
            result["expected_monthly_pension_today_value"],
        )
        self.assertEqual(result["method"], "reverse_required_contribution_with_inflation")

    def test_retirement_monthly_pension_is_inflation_adjusted(self):
        provider = PensionBenchmarkProvider(DEFAULT_PENSION_ASSUMPTIONS)
        pension_profile = PensionProfile(
            current_age=40,
            retirement_age=60,
            expected_monthly_pension=200,
            current_balance=0,
        )

        result = provider.calculate_required_monthly_contribution(pension_profile)

        self.assertAlmostEqual(
            result["inflation_adjusted_monthly_pension_at_retirement"],
            200 * (1.02 ** 20),
            places=6,
        )
        self.assertGreater(
            result["target_capital_at_retirement"],
            result["expected_monthly_pension_today_value"] * result["payout_months"],
        )


if __name__ == "__main__":
    unittest.main()
