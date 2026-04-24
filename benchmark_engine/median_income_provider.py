from benchmark_engine.base_provider import BenchmarkProvider
from benchmark_engine.models import BenchmarkContext, BenchmarkValue


class MedianIncomeProvider(BenchmarkProvider):
    provider_name = "median_income"

    def __init__(self, registry, repository, benchmark_role: str = "median_income"):
        super().__init__(registry, repository)
        self.benchmark_role = benchmark_role

    def provide(self, household_input) -> BenchmarkContext:
        context = BenchmarkContext()
        source = self.registry.find_by_role(self.benchmark_role)
        if source is None:
            context.notes.append("No enabled median income source is registered.")
            return context

        records = self.repository.get_normalized_records(
            source_name=source.source_name,
            metric_name="median_income_by_household_size",
        )
        selected = next(
            (item for item in records if item.household_size == household_input.household_size),
            None,
        )
        if selected is None and records:
            selected = records[-1]
            context.notes.append(
                f"Median income fallback applied: household_size={household_input.household_size} was not found."
            )

        if selected is not None:
            context.add(
                BenchmarkValue(
                    key="median_income_reference",
                    label="가구원수 기준 중위소득",
                    value=selected.value,
                    unit=selected.unit,
                    source_name=selected.source_name,
                    period_year=selected.period_year,
                    method="household_size_lookup",
                    detail={"household_size": selected.household_size},
                )
            )
        return context
