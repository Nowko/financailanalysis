import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from normalizers.models import NormalizedBenchmarkRecord


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_source_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_version TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    period_year INTEGER,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS normalized_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    dataset_key TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    time_grain TEXT NOT NULL,
    period_year INTEGER NOT NULL,
    period_month INTEGER,
    household_scope TEXT NOT NULL,
    household_size INTEGER,
    age_band TEXT,
    statistic TEXT NOT NULL,
    region TEXT NOT NULL,
    currency_unit TEXT NOT NULL,
    attributes_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_update_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    raw_record_id INTEGER,
    normalized_count INTEGER NOT NULL,
    message TEXT NOT NULL,
    source_version TEXT NOT NULL,
    detail_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS manual_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    dataset_key TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    period_year INTEGER NOT NULL,
    household_size INTEGER,
    age_band TEXT,
    override_value REAL NOT NULL,
    unit TEXT NOT NULL,
    reason TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    input_json TEXT NOT NULL,
    benchmark_json TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    summary_text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_normalized_benchmarks_source_metric
ON normalized_benchmarks(source_name, metric_name, period_year);
"""


class BenchmarkDatabase:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)

    def insert_raw_source_data(
        self,
        source_name: str,
        source_type: str,
        source_version: str,
        fetched_at: str,
        period_year: int,
        status: str,
        payload: dict,
        metadata: dict,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO raw_source_data (
                    source_name, source_type, source_version, fetched_at,
                    period_year, status, payload_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_name,
                    source_type,
                    source_version,
                    fetched_at,
                    period_year,
                    status,
                    json.dumps(payload, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def replace_normalized_records(
        self,
        source_name: str,
        period_year: int,
        records: Iterable[NormalizedBenchmarkRecord],
        created_at: str,
    ):
        with self.connect() as connection:
            connection.execute(
                """
                DELETE FROM normalized_benchmarks
                WHERE source_name = ? AND period_year = ?
                """,
                (source_name, period_year),
            )
            connection.executemany(
                """
                INSERT INTO normalized_benchmarks (
                    source_name, dataset_key, metric_name, value, unit, time_grain,
                    period_year, period_month, household_scope, household_size,
                    age_band, statistic, region, currency_unit, attributes_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.source_name,
                        item.dataset_key,
                        item.metric_name,
                        item.value,
                        item.unit,
                        item.time_grain,
                        item.period_year,
                        item.period_month,
                        item.household_scope,
                        item.household_size,
                        item.age_band,
                        item.statistic,
                        item.region,
                        item.currency_unit,
                        json.dumps(item.attributes, ensure_ascii=False),
                        created_at,
                    )
                    for item in records
                ],
            )

    def insert_update_history(
        self,
        source_name: str,
        status: str,
        fetched_at: str,
        raw_record_id: Optional[int],
        normalized_count: int,
        message: str,
        source_version: str,
        detail: dict,
    ):
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO source_update_history (
                    source_name, status, fetched_at, raw_record_id,
                    normalized_count, message, source_version, detail_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_name,
                    status,
                    fetched_at,
                    raw_record_id,
                    normalized_count,
                    message,
                    source_version,
                    json.dumps(detail, ensure_ascii=False),
                ),
            )

    def fetch_normalized_records(
        self,
        metric_name: Optional[str] = None,
        source_name: Optional[str] = None,
        period_year: Optional[int] = None,
    ) -> List[sqlite3.Row]:
        sql = "SELECT * FROM normalized_benchmarks WHERE 1=1"
        params = []
        if metric_name is not None:
            sql += " AND metric_name = ?"
            params.append(metric_name)
        if source_name is not None:
            sql += " AND source_name = ?"
            params.append(source_name)
        if period_year is not None:
            sql += " AND period_year = ?"
            params.append(period_year)
        sql += " ORDER BY period_year DESC, household_size ASC"
        with self.connect() as connection:
            return list(connection.execute(sql, params))

    def fetch_latest_update_status(self) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT h.*
                    FROM source_update_history h
                    INNER JOIN (
                        SELECT source_name, MAX(id) AS max_id
                        FROM source_update_history
                        GROUP BY source_name
                    ) latest
                    ON latest.source_name = h.source_name AND latest.max_id = h.id
                    ORDER BY h.source_name
                    """
                )
            )

    def fetch_manual_overrides(
        self,
        source_name: str,
        metric_name: str,
        period_year: int,
    ) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT *
                    FROM manual_overrides
                    WHERE source_name = ? AND metric_name = ? AND period_year = ? AND active = 1
                    """,
                    (source_name, metric_name, period_year),
                )
            )

    def insert_analysis_snapshot(
        self,
        created_at: str,
        input_payload: dict,
        benchmark_payload: dict,
        analysis_payload: dict,
        summary_text: str,
    ):
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO analysis_snapshots (
                    created_at, input_json, benchmark_json, analysis_json, summary_text
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    json.dumps(input_payload, ensure_ascii=False),
                    json.dumps(benchmark_payload, ensure_ascii=False),
                    json.dumps(analysis_payload, ensure_ascii=False),
                    summary_text,
                ),
            )
