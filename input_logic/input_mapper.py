from models.client_profile import (
    EconomicAssumptions,
    HomePurchaseGoal,
    HouseholdProfile,
    PensionProfile,
    SpecialGoal,
)


def map_to_profile(normalized: dict) -> HouseholdProfile:
    pension = PensionProfile(
        current_age=normalized["pension"]["current_age"],
        retirement_age=normalized["pension"]["retirement_age"],
        expected_monthly_pension=normalized["pension"]["expected_monthly_pension"],
        current_balance=normalized["pension"]["current_balance"],
    )
    economic_assumptions = EconomicAssumptions(**normalized["economic_assumptions"])
    special_goals = [SpecialGoal(**goal) for goal in normalized["special_goals"]]
    home_purchase_goal = HomePurchaseGoal(**normalized["home_purchase_goal"])

    return HouseholdProfile(
        name=normalized.get("name", ""),
        gender=normalized.get("gender", ""),
        birth_year=normalized.get("birth_year", 0),
        birth_month=normalized.get("birth_month", 0),
        birth_day=normalized.get("birth_day", 0),
        age=normalized["age"],
        marital_status=normalized["marital_status"],
        children_count=normalized["children_count"],
        youngest_child_stage=normalized["youngest_child_stage"],
        household_income=normalized["household_income"],
        monthly_expense=normalized["monthly_expense"],
        monthly_debt_payment=normalized["monthly_debt_payment"],
        monthly_saving_investment=normalized["monthly_saving_investment"],
        monthly_emergency_fund=normalized["monthly_emergency_fund"],
        average_consumption=normalized["average_consumption"],
        liquid_assets=normalized["liquid_assets"],
        non_liquid_assets=normalized["non_liquid_assets"],
        economic_assumptions=economic_assumptions,
        special_goals=special_goals,
        expense_categories=normalized["expense_categories"],
        saving_products=normalized["saving_products"],
        insurance_products=normalized["insurance_products"],
        home_purchase_goal=home_purchase_goal,
        pension=pension,
    )
