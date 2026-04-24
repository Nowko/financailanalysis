from benchmark_engine.base_provider import BenchmarkProvider
from benchmark_engine.models import BenchmarkContext


class CompositeBenchmarkProvider(BenchmarkProvider):
    provider_name = "composite"

    def __init__(self, providers):
        self.providers = list(providers)

    def provide(self, household_input) -> BenchmarkContext:
        context = BenchmarkContext()
        for provider in self.providers:
            partial = provider.provide(household_input)
            context.notes.extend(partial.notes)
            for benchmark_value in partial.values.values():
                context.add(benchmark_value)
        return context
