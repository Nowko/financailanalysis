import json
from datetime import datetime
from typing import List, Optional

from collectors.base import CollectedSourceData
from normalizers.models import NormalizedBenchmarkRecord
from source_registry.models import SourceDefinition
from storage.benchmark_db import BenchmarkDatabase


class BenchmarkRepository:
    def __init__(self, db: BenchmarkDatabase):
        self.db = db

    def initialize(self):
        self.db.initialize()

    def store_collected_source(self, source: SourceDefinition, collected: CollectedSourceData):
        raw_record_id = self.db.insert_raw_source_data(
            source_name=source.source_name,
            source_type=source.source_type,
            source_version=source.version,
            fetched_at=collected.fetched_at,
            period_year=collected.period_year,
            status="success",
            payload=collected.raw_payload,
            metadata={
                "benchmark_role": source.benchmark_role,
                "collector_key": source.collector_key,
                "normalizer_key": source.normalizer_key,
                "detail": collected.detail,
            },
        )
        self.db.replace_normalized_records(
            source_name=source.source_name,
            period_year=collected.period_year,
            records=collected.normalized_records,
            created_at=collected.fetched_at,
        )
        self.db.insert_update_history(
            source_name=source.source_name,
            status="success",
            fetched_at=collected.fetched_at,
            raw_record_id=raw_record_id,
            normalized_count=len(collected.normalized_records),
            message=collected.message,
            source_version=source.version,
            detail=collected.detail,
        )

    def list_source_status(self) -> List[dict]:
        return [dict(row) for row in self.db.fetch_latest_update_status()]

    def get_latest_period_year(self, source_name: str, metric_name: Optional[str] = None) -> Optional[int]:
        records = self.db.fetch_normalized_records(metric_name=metric_name, source_name=source_name)
        if not records:
            return None
        return max(int(row["period_year"]) for row in records)

    def get_normalized_records(
        self,
        source_name: str,
        metric_name: Optional[str] = None,
        period_year: Optional[int] = None,
    ) -> List[NormalizedBenchmarkRecord]:
        latest_period_year = period_year
        if latest_period_year is None:
            latest_period_year = self.get_latest_period_year(source_name, metric_name)
        rows = self.db.fetch_normalized_records(
            metric_name=metric_name,
            source_name=source_name,
            period_year=latest_period_year,
        )
        records = []
        for row in rows:
            record = NormalizedBenchmarkRecord(
                source_name=row["source_name"],
                dataset_key=row["dataset_key"],
                metric_name=row["metric_name"],
                value=float(row["value"]),
                unit=row["unit"],
                time_grain=row["time_grain"],
                period_year=int(row["period_year"]),
                period_month=row["period_month"],
                household_scope=row["household_scope"],
                household_size=row["household_size"],
                age_band=row["age_band"],
                statistic=row["statistic"],
                region=row["region"],
                currency_unit=row["currency_unit"],
                attributes=json.loads(row["attributes_json"]),
            )
            records.append(record)

        if latest_period_year is not None and metric_name is not None:
            records = self._apply_manual_overrides(
                source_name=source_name,
                metric_name=metric_name,
                period_year=latest_period_year,
                records=records,
            )
        return records

    def _apply_manual_overrides(
        self,
        source_name: str,
        metric_name: str,
        period_year: int,
        records: List[NormalizedBenchmarkRecord],
    ) -> List[NormalizedBenchmarkRecord]:
        overrides = self.db.fetch_manual_overrides(source_name, metric_name, period_year)
        if not overrides:
            return records

        override_map = {}
        for override in overrides:
            override_map[(override["household_size"], override["age_band"])] = override

        updated_records = []
        for record in records:
            key = (record.household_size, record.age_band)
            override = override_map.get(key)
            if override is None:
                updated_records.append(record)
                continue
            updated = NormalizedBenchmarkRecord(
                **{
                    **record.to_dict(),
                    "value": float(override["override_value"]),
                    "unit": override["unit"],
                    "attributes": {
                        **record.attributes,
                        "override_reason": override["reason"],
                    },
                }
            )
            updated_records.append(updated)
        return updated_records

    def store_analysis_snapshot(self, household_input, benchmark_context, analysis_result, summary_text: str):
        self.db.insert_analysis_snapshot(
            created_at=datetime.utcnow().isoformat(timespec="seconds"),
            input_payload=household_input.to_dict(),
            benchmark_payload=benchmark_context.to_dict(),
            analysis_payload=analysis_result.to_dict(),
            summary_text=summary_text,
        )
