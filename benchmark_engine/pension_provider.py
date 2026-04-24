from benchmark_engine.base_provider import BenchmarkProvider
from benchmark_engine.models import BenchmarkContext


class PensionDerivedProvider(BenchmarkProvider):
    provider_name = "pension_stub"

    def provide(self, household_input) -> BenchmarkContext:
        context = BenchmarkContext()
        if household_input.pension_target_monthly_amount is not None:
            context.notes.append(
                "PensionDerivedProvider is a stub in this MVP. Plug in a reverse-calculation rule later."
            )
        return context
