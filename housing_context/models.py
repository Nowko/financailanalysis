from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class CurrentHomeLoanParameter:
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
        return {
            "key": self.key,
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "as_of_date": self.as_of_date,
            "published_at": self.published_at,
            "source_name": self.source_name,
            "official_url": self.official_url,
            "method": self.method,
            "note": self.note,
        }


@dataclass(frozen=True)
class CurrentHomeLoanContext:
    context_name: str
    as_of_date: str
    parameters: Dict[str, CurrentHomeLoanParameter] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
