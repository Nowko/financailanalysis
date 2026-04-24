from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SourceDefinition:
    source_name: str
    source_type: str
    refresh_cycle: str
    official_url: str
    collector_key: str
    normalizer_key: str
    enabled: bool
    version: str
    benchmark_role: str = ""
    description: str = ""
    config: Dict[str, object] = field(default_factory=dict)


@dataclass
class SourceRegistry:
    sources: Dict[str, SourceDefinition]

    def list_sources(self, enabled_only: bool = False) -> List[SourceDefinition]:
        items = list(self.sources.values())
        if enabled_only:
            items = [item for item in items if item.enabled]
        return sorted(items, key=lambda item: item.source_name)

    def get(self, source_name: str) -> SourceDefinition:
        if source_name not in self.sources:
            raise KeyError(f"Unknown source: {source_name}")
        return self.sources[source_name]

    def find_by_role(self, benchmark_role: str, enabled_only: bool = True) -> Optional[SourceDefinition]:
        for source in self.list_sources(enabled_only=enabled_only):
            if source.benchmark_role == benchmark_role:
                return source
        return None
