import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.analysis_service import AnalysisService
from input_logic.input_mapper import map_to_profile
from input_logic.validators import validate_raw_input
from output_logic.report_builder import bundle_to_dict


class AnalysisServiceTests(unittest.TestCase):
    def test_full_analysis_includes_home_purchase_external_benchmarks_and_report_allocation(self):
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
            "economic_assumptions": {
                "inflation_rate": "3.0",
                "investment_return_rate": "6.0",
                "installment_return_rate": "3.5",
                "pension_accumulation_return_rate": "5.0",
                "pension_payout_return_rate": "2.5",
            },
            "special_goals": [
                {"name": "주택자금", "target_amount": "50,000"},
                {"name": "교육자금", "target_amount": "5,000"},
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
        self.assertEqual(errors, [])
        profile = map_to_profile(normalized)
        analysis = AnalysisService().analyze(profile, warnings)
        payload = bundle_to_dict(profile, analysis)

        self.assertEqual(analysis.benchmark_selection.band_key, "4")
        self.assertEqual(analysis.benchmark_selection.selection_method, "cutoff")
        self.assertEqual(analysis.metric_comparisons["expense"].method, "group_band_lookup")
        self.assertEqual(analysis.saving_product_analysis.product_comparisons["insurance"].actual_amount, 3.0)
        self.assertIn("pension_savings", analysis.saving_product_analysis.tax_benefit_products)
        self.assertAlmostEqual(analysis.saving_product_analysis.total_estimated_tax_benefit_min, 108.0, places=6)
        self.assertAlmostEqual(analysis.saving_product_analysis.total_estimated_tax_benefit_max, 135.0, places=6)
        self.assertEqual(analysis.saving_product_analysis.total_deduction_base_amount, 120.0)
        self.assertAlmostEqual(analysis.home_purchase_result["required_monthly_saving"], 125.0, places=6)
        self.assertGreater(analysis.home_purchase_result["monthly_repayment"], 0.0)

        self.assertIn("expense", analysis.income_allocation_comparisons)
        self.assertAlmostEqual(analysis.income_allocation_comparisons["expense"].benchmark_ratio, 0.601, places=6)
        self.assertAlmostEqual(analysis.income_allocation_comparisons["expense"].actual_ratio, 379.0 / 628.0, places=6)
        self.assertEqual(analysis.dominant_expense_analysis.category_key, "education")
        self.assertEqual(analysis.dominant_expense_analysis.actual_top_category_key, "education")
        self.assertTrue(analysis.dominant_expense_analysis.matches_actual_top)

        self.assertEqual(payload["profile"]["name"], "홍길동")
        self.assertEqual(payload["profile"]["insurance_products"]["life_insurance"], 1.0)
        self.assertEqual(payload["profile"]["home_purchase_goal"]["house_price"], 50000.0)
        self.assertEqual(payload["analysis"]["raw_context"]["total_special_goal_amount"], 55000.0)
        self.assertEqual(payload["analysis"]["raw_context"]["total_insurance_premium"], 3.0)
        self.assertTrue(payload["analysis"]["external_benchmark_summary"]["available"])
        self.assertIn("secondary_benchmarks", payload["analysis"]["metric_comparisons"]["household_income"]["detail"])
        self.assertIn("home_purchase_result", payload["analysis"])
        self.assertEqual(payload["analysis"]["home_purchase_result"]["loan_amount"], 35000.0)
        self.assertIn("tax_benefit_products", payload["analysis"]["saving_product_analysis"])
        self.assertIn("source_report", payload["analysis"])
        self.assertIn("economic_context_summary", payload["analysis"])
        self.assertEqual(payload["analysis"]["economic_context_summary"]["as_of_date"], "2026-04-23")
        self.assertIn("economic_context_summary", payload["analysis"]["raw_context"])
        self.assertIn("income_allocation_comparisons", payload["analysis"])
        self.assertIn("dominant_expense_analysis", payload["analysis"])
        self.assertGreaterEqual(len(payload["analysis"]["source_report"]["sections"]), 4)


if __name__ == "__main__":
    unittest.main()
