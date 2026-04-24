from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class CurrentEconomicMetric:
    key: str
    label: str
    value: float
    unit: str
    as_of_date: str
    published_at: str
    source_name: str
    official_url: str
    method: str
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CurrentEconomicContext:
    context_name: str
    as_of_date: str
    metrics: Dict[str, CurrentEconomicMetric] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    assumption_policy: Dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "context_name": self.context_name,
            "as_of_date": self.as_of_date,
            "metrics": {key: metric.to_dict() for key, metric in self.metrics.items()},
            "notes": list(self.notes),
            "assumption_policy": dict(self.assumption_policy),
        }
