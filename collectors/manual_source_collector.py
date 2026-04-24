import json
from pathlib import Path

from collectors.base import BaseCollector


class ManualSourceCollector(BaseCollector):
    collector_key = "manual"

    def fetch(self, source_definition) -> dict:
        file_path = self.settings.resolve_path(str(source_definition.config["file_path"]))
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
