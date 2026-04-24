import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.home_purchase_engine import calculate_home_purchase_plan


class HomePurchaseEngineTests(unittest.TestCase):
    def test_home_purchase_plan_calculates_saving_and_repayment(self):
        result = calculate_home_purchase_plan(
            house_price=50000,
            ltv=0.7,
            dti=0.4,
            target_years=10,
            loan_term_years=30,
            loan_interest_rate=0.04,
            household_income=628,
        )

        self.assertAlmostEqual(result["down_payment_target"], 15000.0, places=6)
        self.assertAlmostEqual(result["required_monthly_saving"], 125.0, places=6)
        self.assertEqual(result["loan_amount"], 35000.0)
        self.assertGreater(result["monthly_repayment"], 0.0)
        self.assertAlmostEqual(result["dti_limit_payment"], 251.2, places=6)
        self.assertTrue(result["within_dti_limit"])

if __name__ == "__main__":
    unittest.main()
