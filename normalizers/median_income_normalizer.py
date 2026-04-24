from typing import List

from normalizers.base import BaseNormalizer
from normalizers.models import NormalizedBenchmarkRecord


class MedianIncomeNormalizer(BaseNormalizer):
    normalizer_key = "median_income"

    def normalize(self, parsed_payload: dict, source_definition) -> List[NormalizedBenchmarkRecord]:
        dataset_key = str(parsed_payload.get("dataset_key") or source_definition.config.get("dataset_key", "manual"))
        period_year = int(parsed_payload.get("period_year") or source_definition.config.get("period_year", 0))
        unit = str(parsed_payload.get("unit", "만원"))
        records: List[NormalizedBenchmarkRecord] = []

        for row in parsed_payload.get("rows", []):
            records.append(
                NormalizedBenchmarkRecord(
                    source_name=source_definition.source_name,
                    dataset_key=dataset_key,
                    metric_name="median_income_by_household_size",
                    value=float(row["median_income_by_household_size"]),
                    unit=unit,
                    time_grain="monthly",
                    period_year=period_year,
                    household_size=int(row["household_size"]),
                    statistic="median",
                    attributes={
                        "collector": source_definition.collector_key,
                        "benchmark_role": source_definition.benchmark_role,
                    },
                )
            )
        return records
