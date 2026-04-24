from dataclasses import asdict, dataclass, field
from typing import Dict, Optional


@dataclass
class NormalizedBenchmarkRecord:
    source_name: str
    dataset_key: str
    metric_name: str
    value: float
    unit: str
    time_grain: str
    period_year: int
    period_month: Optional[int] = None
    household_scope: str = "household"
    household_size: Optional[int] = None
    age_band: Optional[str] = None
    statistic: str = "mean"
    region: str = "national"
    currency_unit: str = "만원"
    attributes: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
