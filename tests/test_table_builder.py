import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.analysis_service import AnalysisService
from input_logic.input_mapper import map_to_profile
from input_logic.validators import validate_raw_input
from output_logic.report_builder import bundle_to_dict
from output_logic.table_builder import build_analysis_tables


def _build_sample_profile_and_analysis():
    raw = {
        "name": "Tester",
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
        "economic_assumptions": {
            "inflation_rate": "2.0",
            "investment_return_rate": "5.0",
            "installment_return_rate": "3.0",
            "pension_accumulation_return_rate": "4.0",
            "pension_payout_return_rate": "2.0",
        },
        "special_goals": [
            {"name": "주택자금", "target_amount": "50000"},
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
            "house_price": "50,000",
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
    if errors:
        raise AssertionError(errors)
    profile = map_to_profile(normalized)
    analysis = AnalysisService().analyze(profile, warnings)
    return profile, analysis


class TableBuilderTests(unittest.TestCase):
    def test_tables_cover_core_comparisons_and_report_payload(self):
        profile, analysis = _build_sample_profile_and_analysis()

        tables = build_analysis_tables(profile, analysis)
        table_ids = {table["id"] for table in tables}

        self.assertTrue(
            {
                "metrics",
                "income_allocation",
                "emergency",
                "pension",
                "categories",
                "dominant_expense",
                "products",
                "tax_benefits",
                "home_purchase",
                "insurance_detail",
            }.issubset(table_ids)
        )

        product_table = next(table for table in tables if table["id"] == "products")
        insurance_row = next(row for row in product_table["rows"] if row["key"] == "insurance")
        self.assertEqual(insurance_row["tone"], "bad")

        tax_table = next(table for table in tables if table["id"] == "tax_benefits")
        pension_total_row = next(row for row in tax_table["rows"] if row["key"] == "pension_account_total")
        self.assertEqual(pension_total_row["tone"], "good")

        home_table = next(table for table in tables if table["id"] == "home_purchase")
        down_payment_row = next(row for row in home_table["rows"] if row["key"] == "down_payment")
        self.assertEqual(down_payment_row["tone"], "bad")

        dominant_table = next(table for table in tables if table["id"] == "dominant_expense")
        self.assertEqual(dominant_table["rows"][0]["key"], "education")

        report_payload = bundle_to_dict(profile, analysis)
        self.assertIn("comparison_tables", report_payload["analysis"])
        self.assertEqual(report_payload["analysis"]["comparison_tables"][0]["id"], "metrics")


if __name__ == "__main__":
    unittest.main()
