import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from economic_context.service import CurrentEconomicContextService


class CurrentEconomicContextServiceTests(unittest.TestCase):
    def test_recommended_assumptions_are_derived_from_current_context(self):
        service = CurrentEconomicContextService()

        context = service.load_context()
        recommended = service.get_recommended_assumptions()
        summary = service.build_context_summary()

        self.assertEqual(context.as_of_date, "2026-04-23")
        self.assertEqual(recommended["inflation_rate"], 0.022)
        self.assertEqual(recommended["installment_return_rate"], 0.0283)
        self.assertEqual(recommended["investment_return_rate"], 0.0345)
        self.assertEqual(recommended["pension_accumulation_return_rate"], 0.0345)
        self.assertEqual(recommended["pension_payout_return_rate"], 0.025)
        self.assertEqual(summary["applied_assumptions"]["investment_return_rate"], 0.0345)
        self.assertEqual(len(summary["assumption_entries"]), 5)


if __name__ == "__main__":
    unittest.main()
