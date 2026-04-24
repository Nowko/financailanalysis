from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class AnalysisResult:
    income_position: Dict[str, object]
    asset_position: Dict[str, object]
    debt_risk_level: Dict[str, object]
    spending_gap: Dict[str, object]
    household_profile_summary: Dict[str, object]
    benchmark_trace: Dict[str, object]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
