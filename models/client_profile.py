from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class PensionProfile:
    current_age: int
    retirement_age: int
    expected_monthly_pension: float
    current_balance: float = 0.0


@dataclass
class EconomicAssumptions:
    inflation_rate: float
    investment_return_rate: float
    installment_return_rate: float
    pension_accumulation_return_rate: float
    pension_payout_return_rate: float


@dataclass
class SpecialGoal:
    name: str
    target_amount: float
    target_years: int = 0


@dataclass
class HomePurchaseGoal:
    house_price: float = 0.0
    ltv: float = 0.0
    dti: float = 0.0
    target_years: int = 0
    loan_term_years: int = 0
    loan_interest_rate: float = 0.0


@dataclass
class HouseholdProfile:
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    age: int
    marital_status: str
    children_count: int
    youngest_child_stage: str
    household_income: float
    monthly_expense: float
    monthly_debt_payment: float
    monthly_saving_investment: float
    monthly_emergency_fund: float
    average_consumption: float
    liquid_assets: float
    non_liquid_assets: float
    economic_assumptions: EconomicAssumptions
    special_goals: List[SpecialGoal] = field(default_factory=list)
    expense_categories: Dict[str, float] = field(default_factory=dict)
    saving_products: Dict[str, float] = field(default_factory=dict)
    insurance_products: Dict[str, float] = field(default_factory=dict)
    home_purchase_goal: HomePurchaseGoal = field(default_factory=HomePurchaseGoal)
    pension: PensionProfile = None

    @property
    def total_assets(self) -> float:
        return self.liquid_assets + self.non_liquid_assets

    @property
    def total_monthly_outflow(self) -> float:
        return (
            self.monthly_expense
            + self.monthly_debt_payment
            + self.monthly_saving_investment
            + self.monthly_emergency_fund
        )

    @property
    def monthly_surplus(self) -> float:
        return self.household_income - self.total_monthly_outflow

    @property
    def total_special_goal_amount(self) -> float:
        return sum(goal.target_amount for goal in self.special_goals)

    @property
    def total_insurance_premium(self) -> float:
        return sum(self.insurance_products.values())

    def to_dict(self) -> dict:
        data = asdict(self)
        data["total_assets"] = self.total_assets
        data["total_monthly_outflow"] = self.total_monthly_outflow
        data["monthly_surplus"] = self.monthly_surplus
        data["total_special_goal_amount"] = self.total_special_goal_amount
        data["total_insurance_premium"] = self.total_insurance_premium
        return data
