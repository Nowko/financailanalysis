import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.product_analysis_engine import analyze_saving_products
from config import BENCHMARK_PRODUCT_LABELS, PRODUCT_BENCHMARK_CATEGORY_MAP


class ProductAnalysisTests(unittest.TestCase):
    def test_product_bias_tax_benefit_and_insurance_aggregation(self):
        benchmark_payload = {
            "source": "report",
            "method": "monthly_flow_ratio",
            "detail": {"benchmark_key": "monthly_flow_2023"},
            "products": {
                "cash_flow": {"ratio": 0.162, "amount": 17},
                "installment": {"ratio": 0.381, "amount": 40},
                "insurance": {"ratio": 0.362, "amount": 38},
                "investment": {"ratio": 0.095, "amount": 10},
            },
        }
        tax_benefit_payload = {
            "source": "report",
            "tax_source": "국세청 2026",
            "method": "external_tax_rule_lookup",
            "detail": {"references": {}},
            "products": {
                "pension_savings": {
                    "label": "연금저축",
                    "benefit_type": "tax_credit",
                    "annual_cap": 600,
                    "combined_group": "pension_account",
                    "combined_cap": 900,
                    "rates": {"higher_income": 0.12, "lower_income": 0.15},
                },
                "irp": {
                    "label": "IRP",
                    "benefit_type": "tax_credit",
                    "annual_cap": 900,
                    "combined_group": "pension_account",
                    "combined_cap": 900,
                    "rates": {"higher_income": 0.12, "lower_income": 0.15},
                },
                "housing_subscription": {
                    "label": "주택청약종합저축",
                    "benefit_type": "income_deduction",
                    "annual_cap": 300,
                    "deduction_rate": 0.4,
                },
            },
        }
        actual_products = {
            "cash_flow": 5,
            "installment": 0,
            "investment": 0,
            "pension_savings": 50,
            "irp": 25,
            "housing_subscription": 25,
            "indemnity_insurance": 1,
            "life_insurance": 1,
            "variable_insurance": 1,
        }

        result = analyze_saving_products(
            actual_products=actual_products,
            monthly_saving_investment=108,
            benchmark_payload=benchmark_payload,
            benchmark_product_labels=BENCHMARK_PRODUCT_LABELS,
            product_category_map=PRODUCT_BENCHMARK_CATEGORY_MAP,
            tax_benefit_payload=tax_benefit_payload,
        )

        self.assertEqual(result.dominant_product_key, "investment")
        self.assertEqual(result.product_comparisons["installment"].actual_amount, 25.0)
        self.assertEqual(result.product_comparisons["insurance"].actual_amount, 3.0)
        self.assertEqual(result.product_comparisons["investment"].actual_amount, 75.0)
        self.assertEqual(result.product_comparisons["investment"].status, "overweight")

        pension_savings = result.tax_benefit_products["pension_savings"]
        irp = result.tax_benefit_products["irp"]
        housing_subscription = result.tax_benefit_products["housing_subscription"]

        self.assertEqual(pension_savings.benefit_base_amount, 600.0)
        self.assertAlmostEqual(pension_savings.estimated_benefit_min, 72.0, places=6)
        self.assertAlmostEqual(pension_savings.estimated_benefit_max, 90.0, places=6)
        self.assertEqual(irp.benefit_base_amount, 300.0)
        self.assertAlmostEqual(result.total_estimated_tax_benefit_min, 108.0, places=6)
        self.assertAlmostEqual(result.total_estimated_tax_benefit_max, 135.0, places=6)
        self.assertEqual(housing_subscription.deduction_base_amount, 120.0)
        self.assertTrue(housing_subscription.narrative)


if __name__ == "__main__":
    unittest.main()
