import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from input_logic.validators import validate_raw_input


class ValidatorTests(unittest.TestCase):
    def test_birth_year_only_derives_age_and_normalizes_new_sections(self):
        raw = {
            "name": "홍길동",
            "gender": "male",
            "birth_year": "1988",
            "birth_month": "",
            "birth_day": "",
            "age": "",
            "marital_status": "single",
            "children_count": "",
            "youngest_child_stage": "",
            "household_income": "5,000",
            "monthly_expense": "2,000",
            "monthly_debt_payment": "300",
            "monthly_saving_investment": "108",
            "monthly_emergency_fund": "200",
            "average_consumption": "2,000",
            "liquid_assets": "8,000",
            "non_liquid_assets": "20,000",
            "economic_assumptions": {
                "inflation_rate": "2.0",
                "investment_return_rate": "5.0",
                "installment_return_rate": "3.0",
                "pension_accumulation_return_rate": "4.0",
                "pension_payout_return_rate": "2.0",
            },
            "special_goals": [{"name": "주택자금", "target_amount": "50,000"}],
            "expense_categories": {
                "food": "1,000",
                "housing": "1,000",
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
            "pension": {},
        }

        normalized, errors, warnings = validate_raw_input(raw)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(normalized["birth_year"], 1988)
        self.assertEqual(normalized["age"], 38)
        self.assertEqual(normalized["economic_assumptions"]["inflation_rate"], 0.02)
        self.assertEqual(normalized["special_goals"][0]["target_amount"], 50000.0)
        self.assertEqual(normalized["special_goals"][0]["target_years"], 10)
        self.assertEqual(normalized["insurance_products"]["life_insurance"], 1.0)
        self.assertEqual(normalized["saving_products"]["housing_subscription"], 25.0)
        self.assertEqual(normalized["home_purchase_goal"]["house_price"], 50000.0)
        self.assertEqual(normalized["home_purchase_goal"]["ltv"], 0.7)

    def test_age_only_derives_birth_year(self):
        raw = {
            "name": "홍길동",
            "gender": "male",
            "birth_year": "",
            "birth_month": "",
            "birth_day": "",
            "age": "38",
            "marital_status": "single",
            "children_count": "",
            "youngest_child_stage": "",
            "household_income": "5,000",
            "monthly_expense": "2,000",
            "monthly_debt_payment": "300",
            "monthly_saving_investment": "108",
            "monthly_emergency_fund": "200",
            "average_consumption": "2,000",
            "liquid_assets": "8,000",
            "non_liquid_assets": "20,000",
            "economic_assumptions": {},
            "special_goals": [],
            "expense_categories": {
                "food": "1,000",
                "housing": "1,000",
            },
            "saving_products": {
                "cash_flow": "5",
                "installment": "0",
                "investment": "0",
                "pension_savings": "50",
                "irp": "25",
                "housing_subscription": "25",
            },
            "insurance_products": {},
            "home_purchase_goal": {},
            "pension": {},
        }

        normalized, errors, warnings = validate_raw_input(raw)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(normalized["age"], 38)
        self.assertEqual(normalized["birth_year"], 1988)
        self.assertEqual(normalized["economic_assumptions"]["inflation_rate"], 0.022)
        self.assertEqual(normalized["economic_assumptions"]["investment_return_rate"], 0.0345)
        self.assertEqual(normalized["economic_assumptions"]["installment_return_rate"], 0.0283)
        self.assertEqual(normalized["economic_assumptions"]["pension_accumulation_return_rate"], 0.0345)
        self.assertEqual(normalized["economic_assumptions"]["pension_payout_return_rate"], 0.025)
        self.assertEqual(normalized["home_purchase_goal"]["target_years"], 10)
        self.assertEqual(normalized["home_purchase_goal"]["ltv"], 0.7)
        self.assertEqual(normalized["home_purchase_goal"]["dti"], 0.4)
        self.assertEqual(normalized["home_purchase_goal"]["loan_term_years"], 30)
        self.assertEqual(normalized["home_purchase_goal"]["loan_interest_rate"], 0.0426)

    def test_birth_year_or_age_is_required(self):
        raw = {
            "name": "홍길동",
            "gender": "male",
            "birth_year": "",
            "birth_month": "",
            "birth_day": "",
            "age": "",
            "marital_status": "single",
            "children_count": "",
            "youngest_child_stage": "",
            "household_income": "5,000",
            "monthly_expense": "2,000",
            "monthly_debt_payment": "300",
            "monthly_saving_investment": "108",
            "monthly_emergency_fund": "200",
            "average_consumption": "2,000",
            "liquid_assets": "8,000",
            "non_liquid_assets": "20,000",
            "economic_assumptions": {},
            "special_goals": [],
            "expense_categories": {
                "food": "1,000",
                "housing": "1,000",
            },
            "saving_products": {},
            "insurance_products": {},
            "home_purchase_goal": {},
            "pension": {},
        }

        _, errors, _ = validate_raw_input(raw)

        self.assertIn("출생년도 또는 나이 중 하나는 입력해야 합니다.", errors)

    def test_warning_cases_are_collected(self):
        raw = {
            "birth_year": "",
            "birth_month": "",
            "birth_day": "",
            "age": "45",
            "marital_status": "married",
            "children_count": "1",
            "youngest_child_stage": "middle_high",
            "household_income": "300",
            "monthly_expense": "200",
            "monthly_debt_payment": "50",
            "monthly_saving_investment": "100",
            "monthly_emergency_fund": "40",
            "average_consumption": "200",
            "liquid_assets": "100",
            "non_liquid_assets": "1000",
            "economic_assumptions": {},
            "special_goals": [],
            "expense_categories": {},
            "saving_products": {},
            "insurance_products": {},
            "home_purchase_goal": {},
            "pension": {
                "current_age": "45",
                "retirement_age": "40",
                "expected_monthly_pension": "150",
                "current_balance": "1000",
            },
        }

        _, errors, warnings = validate_raw_input(raw)

        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 4)

    def test_single_household_disables_child_values_in_normalization(self):
        raw = {
            "name": "홍길동",
            "gender": "male",
            "birth_year": "",
            "birth_month": "",
            "birth_day": "",
            "age": "38",
            "marital_status": "single",
            "children_count": "2",
            "youngest_child_stage": "college",
            "household_income": "5,000",
            "monthly_expense": "2,000",
            "monthly_debt_payment": "300",
            "monthly_saving_investment": "108",
            "monthly_emergency_fund": "200",
            "average_consumption": "2,000",
            "liquid_assets": "8,000",
            "non_liquid_assets": "20,000",
            "economic_assumptions": {},
            "special_goals": [{"name": "생활안정자금", "target_amount": "3,000"}],
            "expense_categories": {
                "food": "1,000",
                "housing": "1,000",
            },
            "saving_products": {},
            "insurance_products": {},
            "home_purchase_goal": {},
            "pension": {},
        }

        normalized, errors, warnings = validate_raw_input(raw)

        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("상품별 합계(0)", warnings[0])
        self.assertEqual(normalized["children_count"], 0)
        self.assertEqual(normalized["youngest_child_stage"], "none")
        self.assertEqual(normalized["household_income"], 5000.0)
        self.assertEqual(normalized["special_goals"][0]["name"], "생활안정자금")


if __name__ == "__main__":
    unittest.main()
