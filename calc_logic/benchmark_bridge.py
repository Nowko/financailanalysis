from typing import Dict, List

from analysis_engine.comparator import HouseholdAnalysisEngine
from benchmark_engine.service import build_default_benchmark_provider
from benchmark_settings import load_benchmark_settings
from collectors.factory import get_collector
from input_engine.validators import parse_household_input
from normalizers.factory import get_normalizer
from source_registry.loader import load_source_registry
from storage.benchmark_db import BenchmarkDatabase
from storage.benchmark_repository import BenchmarkRepository


def _derive_household_size(profile) -> int:
    adult_count = 2 if profile.marital_status == "married" else 1
    return max(adult_count + int(profile.children_count or 0), 1)


def _build_household_payload(profile) -> Dict[str, object]:
    notes: List[str] = []
    if getattr(profile, "monthly_debt_payment", 0.0) > 0:
        notes.append(
            "공공통계 총부채 비교에는 부채 총액 입력값이 필요하지만, 현재 메인 입력은 월 상환액 중심이라 총부채는 0으로 처리했습니다."
        )

    disposable_income = max(
        float(profile.household_income)
        - float(profile.monthly_debt_payment)
        - float(profile.monthly_saving_investment)
        - float(profile.monthly_emergency_fund),
        0.0,
    )
    return {
        "household_size": _derive_household_size(profile),
        "reference_age": profile.age,
        "monthly_income": profile.household_income,
        "disposable_income": disposable_income,
        "total_assets": profile.total_assets,
        "financial_assets": profile.liquid_assets,
        "real_estate_assets": profile.non_liquid_assets,
        "total_debt": 0.0,
        "monthly_consumption": profile.monthly_expense,
        "pension_monthly_contribution": float(profile.saving_products.get("pension_savings", 0.0))
        + float(profile.saving_products.get("irp", 0.0)),
        "pension_current_age": profile.pension.current_age if profile.pension else None,
        "pension_retirement_age": profile.pension.retirement_age if profile.pension else None,
        "pension_target_monthly_amount": profile.pension.expected_monthly_pension if profile.pension else None,
        "metadata": {
            "main_analysis_bridge": True,
            "bridge_notes": notes,
        },
    }


class MainAnalysisBenchmarkBridge:
    def __init__(self):
        self.settings = load_benchmark_settings()
        self.registry = load_source_registry(self.settings.registry_path)
        self.repository = BenchmarkRepository(BenchmarkDatabase(self.settings.db_path))
        self.repository.initialize()
        self._seed_enabled_sources()
        self.provider = build_default_benchmark_provider(self.registry, self.repository)
        self.analysis_engine = HouseholdAnalysisEngine(self.provider)

    def _seed_enabled_sources(self):
        existing_status = {row["source_name"] for row in self.repository.list_source_status()}
        for source in self.registry.list_sources(enabled_only=True):
            if source.source_name in existing_status:
                continue
            collector = get_collector(source.collector_key, self.settings)
            normalizer = get_normalizer(source.normalizer_key)
            collected = collector.collect(source, normalizer)
            self.repository.store_collected_source(source, collected)

    def analyze_profile(self, profile) -> Dict[str, object]:
        try:
            household_payload = _build_household_payload(profile)
            household_input = parse_household_input(household_payload)
            benchmark_context, analysis_result = self.analysis_engine.analyze(household_input)
            source_status = self.repository.list_source_status()
            used_sources = []
            for key, value in benchmark_context.values.items():
                used_sources.append(
                    {
                        "benchmark_key": key,
                        "source_name": value.source_name,
                        "period_year": value.period_year,
                        "method": value.method,
                    }
                )

            return {
                "available": bool(benchmark_context.values),
                "household_input": household_input.to_dict(),
                "benchmark_context": benchmark_context.to_dict(),
                "analysis": analysis_result.to_dict(),
                "source_status": source_status,
                "used_sources": used_sources,
                "notes": list(analysis_result.notes) + list(household_input.metadata.get("bridge_notes", [])),
            }
        except Exception as exc:
            return {
                "available": False,
                "household_input": {},
                "benchmark_context": {"values": {}, "notes": []},
                "analysis": {},
                "source_status": self.repository.list_source_status(),
                "used_sources": [],
                "notes": [f"외부 benchmark 연동에 실패했습니다: {exc}"],
            }
