import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from collectors.base import BaseCollector


class KosisCollector(BaseCollector):
    collector_key = "kosis"

    def fetch(self, source_definition) -> dict:
        mode = str(source_definition.config.get("mode", "mock")).strip().lower()
        if self.settings.kosis_use_mock or mode == "mock":
            mock_path = self.settings.resolve_path(str(source_definition.config["mock_response_path"]))
            return json.loads(Path(mock_path).read_text(encoding="utf-8"))

        api_url = str(source_definition.config.get("api_url", "")).strip()
        if not api_url:
            raise ValueError(
                "KOSIS api_url is not configured. Provide it in the source registry config or use mock mode."
            )

        params = dict(source_definition.config.get("params", {}))
        api_key_param_name = str(source_definition.config.get("api_key_param_name", "")).strip()
        if api_key_param_name and self.settings.kosis_api_key:
            params[api_key_param_name] = self.settings.kosis_api_key

        query_string = urlencode(params)
        request_url = api_url if not query_string else f"{api_url}?{query_string}"
        with urlopen(request_url) as response:
            return json.loads(response.read().decode("utf-8"))
