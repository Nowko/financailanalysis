import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.expense_planning_engine import calculate_expense_plan_summary, resolve_category_total


class ExpensePlanningEngineTests(unittest.TestCase):
    def test_resolve_category_total_prefers_detail_sum_when_present(self):
        resolved = resolve_category_total(
            manual_total=40.0,
            detail_values={
                "daily_food": 12.0,
                "weekly_food": 8.0,
                "delivery_food": 5.0,
            },
        )
        self.assertEqual(resolved, 25.0)

    def test_resolve_category_total_keeps_manual_total_without_detail_values(self):
        resolved = resolve_category_total(
            manual_total=40.0,
            detail_values={
                "daily_food": 0.0,
                "weekly_food": 0.0,
            },
        )
        self.assertEqual(resolved, 40.0)

    def test_resolve_category_total_applies_daily_multiplier(self):
        resolved = resolve_category_total(
            manual_total=0.0,
            detail_values={
                "daily_food": 1.0,
                "delivery_food": 10.0,
            },
            multipliers={
                "daily_food": 30.0,
            },
        )
        self.assertEqual(resolved, 40.0)

    def test_calculate_expense_plan_summary_includes_allocation_gap(self):
        summary = calculate_expense_plan_summary(
            category_totals={
                "food": 100.0,
                "transport": 20.0,
                "housing": 80.0,
            },
            household_income=300.0,
            saving_products={
                "cash_flow": 10.0,
                "installment": 15.0,
                "investment": 20.0,
                "pension_savings": 25.0,
                "irp": 10.0,
                "housing_subscription": 5.0,
            },
            insurance_products={
                "indemnity_insurance": 3.0,
                "life_insurance": 7.0,
                "variable_insurance": 0.0,
            },
            labels={
                "cash_flow": "수시입출금/CMA",
                "installment": "적금/청약",
                "investment": "투자상품",
                "pension_savings": "연금저축",
                "irp": "IRP",
                "housing_subscription": "주택청약",
                "indemnity_insurance": "실손",
                "life_insurance": "생보",
                "variable_insurance": "변액",
            },
            ordered_keys=(
                "cash_flow",
                "installment",
                "investment",
                "pension_savings",
                "irp",
                "housing_subscription",
                "indemnity_insurance",
                "life_insurance",
                "variable_insurance",
            ),
        )

        self.assertEqual(summary["expense_total"], 200.0)
        self.assertEqual(summary["available_cash"], 100.0)
        self.assertEqual(summary["allocation_total"], 95.0)
        self.assertEqual(summary["allocation_gap"], 5.0)
        self.assertEqual(summary["allocation_rows"][0]["label"], "수시입출금/CMA")
        self.assertEqual(summary["allocation_rows"][6]["amount"], 3.0)


if __name__ == "__main__":
    unittest.main()
