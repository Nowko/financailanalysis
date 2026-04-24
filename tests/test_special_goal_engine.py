import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.special_goal_engine import build_special_goal_saving_plan, calculate_required_monthly_saving


class SpecialGoalEngineTests(unittest.TestCase):
    def test_required_monthly_saving_handles_zero_rate(self):
        result = calculate_required_monthly_saving(target_amount=1200, annual_rate=0.0, years=10)
        self.assertAlmostEqual(result, 10.0, places=6)

    def test_build_special_goal_saving_plan_uses_per_goal_target_years(self):
        rows = build_special_goal_saving_plan(
            goals=[
                {"name": "주택자금", "target_amount": 50000, "target_years": 10},
                {"name": "교육자금", "target_amount": 5000, "target_years": 8},
                {"name": "여행자금", "target_amount": 1200, "target_years": 2},
            ],
            installment_return_rate=0.03,
            investment_return_rate=0.04,
            excluded_names={"주택자금"},
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "교육자금")
        self.assertEqual(rows[0]["target_years"], 8)
        self.assertEqual(rows[1]["target_years"], 2)
        self.assertGreater(rows[1]["installment_monthly_saving"], rows[0]["installment_monthly_saving"])
        self.assertGreater(rows[0]["investment_monthly_saving"], 0.0)
        self.assertLess(rows[0]["investment_monthly_saving"], rows[0]["installment_monthly_saving"])


if __name__ == "__main__":
    unittest.main()
