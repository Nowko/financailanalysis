from benchmark_engine.base_provider import BenchmarkProvider
from benchmark_engine.models import BenchmarkContext, BenchmarkValue


PEER_METRIC_MAP = {
    "monthly_income": ("peer_monthly_income", "동일 조건 월소득 평균"),
    "disposable_income": ("peer_disposable_income", "동일 조건 가처분소득 평균"),
    "total_assets": ("peer_total_assets", "동일 조건 총자산 평균"),
    "financial_assets": ("peer_financial_assets", "동일 조건 금융자산 평균"),
    "real_estate_assets": ("peer_real_estate_assets", "동일 조건 부동산자산 평균"),
    "total_debt": ("peer_total_debt", "동일 조건 총부채 평균"),
    "monthly_consumption": ("peer_monthly_consumption", "동일 조건 월소비지출 평균"),
}


class KosisBenchmarkProvider(BenchmarkProvider):
    provider_name = "kosis_peer"

    def __init__(self, registry, repository, benchmark_role: str = "household_peer_stats"):
        super().__init__(registry, repository)
        self.benchmark_role = benchmark_role

    def _pick_best_record(self, records, household_input):
        if not records:
            return None

        exact = [
            item
            for item in records
            if item.household_size == household_input.household_size and item.age_band == household_input.age_band
        ]
        if exact:
            return exact[0]

        household_only = [item for item in records if item.household_size == household_input.household_size]
        if household_only:
            return household_only[0]

        age_only = [item for item in records if item.age_band == household_input.age_band]
        if age_only:
            return age_only[0]

        return records[0]

    def provide(self, household_input) -> BenchmarkContext:
        context = BenchmarkContext()
        source = self.registry.find_by_role(self.benchmark_role)
        if source is None:
            context.notes.append("No enabled KOSIS household peer source is registered.")
            return context

        for metric_name, (key, label) in PEER_METRIC_MAP.items():
            records = self.repository.get_normalized_records(
                source_name=source.source_name,
                metric_name=metric_name,
            )
            selected = self._pick_best_record(records, household_input)
            if selected is None:
                context.notes.append(f"{metric_name} benchmark is missing in source {source.source_name}.")
                continue
            context.add(
                BenchmarkValue(
                    key=key,
                    label=label,
                    value=selected.value,
                    unit=selected.unit,
                    source_name=selected.source_name,
                    period_year=selected.period_year,
                    method="household_size_age_band_lookup",
                    detail={
                        "household_size": selected.household_size,
                        "age_band": selected.age_band,
                    },
                )
            )

        return context
