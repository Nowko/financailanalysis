import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from housing_context.service import CurrentHomeLoanContextService


class CurrentHomeLoanContextServiceTests(unittest.TestCase):
    def test_recommended_home_loan_defaults_are_loaded(self):
        service = CurrentHomeLoanContextService()

        context = service.load_context()
        defaults = service.get_recommended_defaults()
        input_defaults = service.build_default_input_map()

        self.assertEqual(context.as_of_date, "2026-04-23")
        self.assertEqual(defaults["ltv"], 0.7)
        self.assertEqual(defaults["dti"], 0.4)
        self.assertEqual(defaults["loan_term_years"], 30)
        self.assertEqual(defaults["loan_interest_rate"], 0.0426)
        self.assertEqual(input_defaults["ltv"], 70.0)
        self.assertEqual(input_defaults["loan_interest_rate"], 4.26)


if __name__ == "__main__":
    unittest.main()
