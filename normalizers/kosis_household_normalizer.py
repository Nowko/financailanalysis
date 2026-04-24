from typing import List

from normalizers.base import BaseNormalizer
from normalizers.models import NormalizedBenchmarkRecord


KOSIS_METRIC_MAP = {
    "monthly_income": {"time_grain": "monthly", "statistic": "mean"},
    "disposable_income": {"time_grain": "monthly", "statistic": "mean"},
    "total_assets": {"time_grain": "point_in_time", "statistic": "mean"},
    "financial_assets": {"time_grain": "point_in_time", "statistic": "mean"},
    "real_estate_assets": {"time_grain": "point_in_time", "statistic": "mean"},
    "total_debt": {"time_grain": "point_in_time", "statistic": "mean"},
    "monthly_consumption": {"time_grain": "monthly", "statistic": "mean"},
}


class KosisHouseholdSurveyNormalizer(BaseNormalizer):
    normalizer_key = "kosis_household"

    def normalize(self, parsed_payload: dict, source_definition) -> List[NormalizedBenchmarkRecord]:
        dataset_key = str(parsed_payload.get("dataset_key") or source_definition.config.get("dataset_key", "kosis"))
        period_year = int(parsed_payload.get("period_year") or source_definition.config.get("period_year", 0))
        unit = str(parsed_payload.get("unit", "만원"))
        rows = parsed_payload.get("rows", [])
        records: List[NormalizedBenchmarkRecord] = []

        for row in rows:
            household_size = int(row.get("household_size")) if row.get("household_size") is not None else None
            age_band = row.get("age_band")
            for metric_name, meta in KOSIS_METRIC_MAP.items():
                if metric_name not in row:
                    continue
                records.append(
                    NormalizedBenchmarkRecord(
                        source_name=source_definition.source_name,
                        dataset_key=dataset_key,
                        metric_name=metric_name,
                        value=float(row[metric_name]),
                        unit=unit,
                        time_grain=meta["time_grain"],
                        period_year=period_year,
                        household_size=household_size,
                        age_band=age_band,
                        statistic=meta["statistic"],
                        attributes={
                            "collector": source_definition.collector_key,
                            "benchmark_role": source_definition.benchmark_role,
                        },
                    )
                )
        return records
