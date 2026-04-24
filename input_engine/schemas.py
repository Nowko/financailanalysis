from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class HouseholdInput:
    household_size: int
    reference_age: int
    age_band: str
    monthly_income: float
    disposable_income: float
    total_assets: float
    financial_assets: float
    real_estate_assets: float
    total_debt: float
    monthly_consumption: float
    pension_monthly_contribution: float = 0.0
    pension_current_age: Optional[int] = None
    pension_retirement_age: Optional[int] = None
    pension_target_monthly_amount: Optional[float] = None
    metadata: Dict[str, object] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def monthly_surplus(self) -> float:
        return self.disposable_income - self.monthly_consumption

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["monthly_surplus"] = self.monthly_surplus
        return payload
