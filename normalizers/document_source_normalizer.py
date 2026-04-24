from typing import List

from normalizers.base import BaseNormalizer
from normalizers.models import NormalizedBenchmarkRecord


class DocumentSourceNormalizer(BaseNormalizer):
    normalizer_key = "document_table"

    def normalize(self, parsed_payload: dict, source_definition) -> List[NormalizedBenchmarkRecord]:
        dataset_key = str(parsed_payload.get("dataset_key") or source_definition.config.get("dataset_key", "document"))
        period_year = int(parsed_payload.get("period_year") or source_definition.config.get("period_year", 0))
        rows = parsed_payload.get("rows", [])
        records: List[NormalizedBenchmarkRecord] = []

        for row in rows:
            records.append(
                NormalizedBenchmarkRecord(
                    source_name=source_definition.source_name,
                    dataset_key=dataset_key,
                    metric_name=str(row["metric_name"]),
                    value=float(row["value"]),
                    unit=str(row.get("unit", "만원")),
                    time_grain=str(row.get("time_grain", "point_in_time")),
                    period_year=period_year,
                    household_size=(
                        int(row["household_size"])
                        if row.get("household_size") not in ("", None)
                        else None
                    ),
                    age_band=row.get("age_band"),
                    statistic=str(row.get("statistic", "reference")),
                    attributes={
                        "segment": row.get("segment", ""),
                        "collector": source_definition.collector_key,
                        "benchmark_role": source_definition.benchmark_role,
                    },
                )
            )
        return records
