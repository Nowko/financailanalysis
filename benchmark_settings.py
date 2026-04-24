import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass
class BenchmarkSettings:
    base_dir: Path
    db_path: Path
    registry_path: Path
    kosis_api_key: str
    kosis_use_mock: bool

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.base_dir / path


def _to_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def load_benchmark_settings() -> BenchmarkSettings:
    db_path = os.environ.get("BENCHMARK_DB_PATH", "data/benchmark_data.sqlite3")
    registry_path = os.environ.get(
        "BENCHMARK_SOURCE_REGISTRY_PATH",
        "data/source_registry/benchmark_sources.json",
    )
    return BenchmarkSettings(
        base_dir=BASE_DIR,
        db_path=BASE_DIR / db_path,
        registry_path=BASE_DIR / registry_path,
        kosis_api_key=os.environ.get("KOSIS_API_KEY", ""),
        kosis_use_mock=_to_bool(os.environ.get("KOSIS_USE_MOCK"), True),
    )
