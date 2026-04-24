from typing import List

from normalizers.models import NormalizedBenchmarkRecord


class BaseNormalizer:
    normalizer_key = "base"

    def normalize(self, parsed_payload: dict, source_definition) -> List[NormalizedBenchmarkRecord]:
        raise NotImplementedError
