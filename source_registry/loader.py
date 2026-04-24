import json
from pathlib import Path

from source_registry.models import SourceDefinition, SourceRegistry


def load_source_registry(path: Path) -> SourceRegistry:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = {}
    for item in payload.get("sources", []):
        source = SourceDefinition(
            source_name=item["source_name"],
            source_type=item["source_type"],
            refresh_cycle=item["refresh_cycle"],
            official_url=item["official_url"],
            collector_key=item["collector_key"],
            normalizer_key=item["normalizer_key"],
            enabled=bool(item.get("enabled", True)),
            version=str(item.get("version", "")),
            benchmark_role=str(item.get("benchmark_role", "")),
            description=str(item.get("description", "")),
            config=dict(item.get("config", {})),
        )
        sources[source.source_name] = source
    return SourceRegistry(sources=sources)
