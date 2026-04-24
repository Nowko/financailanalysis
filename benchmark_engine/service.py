from benchmark_engine.composite_provider import CompositeBenchmarkProvider
from benchmark_engine.kosis_provider import KosisBenchmarkProvider
from benchmark_engine.median_income_provider import MedianIncomeProvider
from benchmark_engine.pension_provider import PensionDerivedProvider


def build_default_benchmark_provider(registry, repository) -> CompositeBenchmarkProvider:
    return CompositeBenchmarkProvider(
        providers=[
            KosisBenchmarkProvider(registry, repository),
            MedianIncomeProvider(registry, repository),
            PensionDerivedProvider(registry, repository),
        ]
    )
