from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class BenchmarkValue:
    key: str
    label: str
    value: float
    unit: str
    source_name: str
    period_year: int
    method: str
    detail: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BenchmarkContext:
    values: Dict[str, BenchmarkValue] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def add(self, benchmark_value: BenchmarkValue):
        self.values[benchmark_value.key] = benchmark_value

    def to_dict(self) -> dict:
        return {
            "values": {key: value.to_dict() for key, value in self.values.items()},
            "notes": list(self.notes),
        }
