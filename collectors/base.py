from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from normalizers.models import NormalizedBenchmarkRecord


@dataclass
class CollectedSourceData:
    source_name: str
    source_type: str
    source_version: str
    fetched_at: str
    raw_payload: dict
    parsed_payload: dict
    normalized_records: List[NormalizedBenchmarkRecord]
    period_year: int
    message: str = ""
    detail: dict = field(default_factory=dict)


class BaseCollector:
    collector_key = "base"

    def __init__(self, settings):
        self.settings = settings

    def fetch(self, source_definition) -> dict:
        raise NotImplementedError

    def parse(self, fetched_payload: dict, source_definition) -> dict:
        return fetched_payload

    def collect(self, source_definition, normalizer) -> CollectedSourceData:
        fetched_payload = self.fetch(source_definition)
        parsed_payload = self.parse(fetched_payload, source_definition)
        normalized_records = normalizer.normalize(parsed_payload, source_definition)
        period_year = int(
            parsed_payload.get("period_year")
            or source_definition.config.get("period_year", 0)
        )
        return CollectedSourceData(
            source_name=source_definition.source_name,
            source_type=source_definition.source_type,
            source_version=source_definition.version,
            fetched_at=datetime.utcnow().isoformat(timespec="seconds"),
            raw_payload=fetched_payload,
            parsed_payload=parsed_payload,
            normalized_records=normalized_records,
            period_year=period_year,
            message=f"{source_definition.source_name} collected successfully.",
            detail={"record_count": len(normalized_records)},
        )
