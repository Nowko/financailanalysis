import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.analysis_service import AnalysisService
from config import CATEGORY_LABELS
from input_logic.input_mapper import map_to_profile
from input_logic.validators import validate_raw_input
from output_logic.sentence_builder import build_summary_text


class SentenceBuilderTests(unittest.TestCase):
    def test_summary_includes_housing_note_income_allocation_and_dominant_expense(self):
        raw = {
            "name": "홍길동",
            "gender": "male",
            "birth_year": "",
            "birth_month": "",
            "birth_day": "",
            "age": "45",
            "marital_status": "married",
            "children_count": "1",
            "youngest_child_stage": "middle_high",
            "household_income": "628",
            "monthly_expense": "379",
            "monthly_debt_payment": "53",
            "monthly_saving_investment": "108",
            "monthly_emergency_fund": "88",
            "average_consumption": "379",
            "liquid_assets": "8055",
            "non_liquid_assets": "68962",
            "economic_assumptions": {},
            "special_goals": [
                {"name": "주택자금", "target_amount": "50000", "target_years": "10"},
            ],
            "expense_categories": {
                "food": "89",
                "transport": "30",
                "utilities": "30",
                "communication": "20",
                "housing": "69",
                "leisure": "21",
                "fashion": "21",
                "social": "22",
                "allowance": "39",
                "education": "97",
                "medical": "26",
            },
            "saving_products": {
                "cash_flow": "5",
                "installment": "0",
                "investment": "0",
                "pension_savings": "50",
                "irp": "25",
                "housing_subscription": "25",
            },
            "insurance_products": {
                "indemnity_insurance": "1",
                "life_insurance": "1",
                "variable_insurance": "1",
            },
            "home_purchase_goal": {
                "house_price": "50000",
                "ltv": "70",
                "dti": "40",
                "target_years": "10",
                "loan_term_years": "30",
                "loan_interest_rate": "4.0",
            },
            "pension": {
                "current_age": "45",
                "retirement_age": "60",
                "expected_monthly_pension": "200",
                "current_balance": "3000",
            },
        }

        normalized, errors, warnings = validate_raw_input(raw)
        self.assertEqual(errors, [])
        profile = map_to_profile(normalized)
        analysis = AnalysisService().analyze(profile, warnings)

        text = build_summary_text(profile, analysis)

        self.assertIn("주거비는 월세성 주거비 기준", text)
        self.assertIn("고정소비율:", text)
        self.assertIn("[소득운용 분석]", text)
        self.assertIn("[대표 정기지출]", text)
        self.assertIn("교육비", text)
        self.assertEqual(CATEGORY_LABELS["housing"], "주거비(월세성)")


if __name__ == "__main__":
    unittest.main()
