from benchmark_engine.models import BenchmarkContext


class BenchmarkProvider:
    provider_name = "base"

    def __init__(self, registry, repository):
        self.registry = registry
        self.repository = repository

    def provide(self, household_input) -> BenchmarkContext:
        raise NotImplementedError
