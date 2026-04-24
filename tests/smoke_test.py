import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.analysis_service import AnalysisService
from input_logic.input_mapper import map_to_profile
from input_logic.validators import validate_raw_input


def main():
    raw = {
        "name": "홍길동",
        "gender": "male",
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
    assert not errors, errors
    profile = map_to_profile(normalized)
    analysis = AnalysisService().analyze(profile, warnings)
    assert analysis.metric_comparisons["expense"].benchmark_value > 0
    assert analysis.pension_result["required_monthly_contribution"] >= 0
    assert analysis.raw_context["total_special_goal_amount"] == 50000.0
    assert analysis.raw_context["total_insurance_premium"] == 3.0
    assert analysis.home_purchase_result["loan_amount"] == 35000.0
    assert "pension_savings" in analysis.saving_product_analysis.tax_benefit_products
    print("smoke_test_ok")


if __name__ == "__main__":
    main()
