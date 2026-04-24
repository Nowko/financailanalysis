from dataclasses import asdict

from calc_logic.benchmark_bridge import MainAnalysisBenchmarkBridge
from calc_logic.comparison_engine import compare_metric
from calc_logic.expense_detail_engine import build_category_comparisons
from calc_logic.home_purchase_engine import calculate_home_purchase_plan
from calc_logic.income_allocation_engine import (
    build_dominant_expense_analysis,
    build_income_allocation_comparisons,
)
from calc_logic.product_analysis_engine import analyze_saving_products
from calc_logic.providers.pension_provider import PensionBenchmarkProvider
from calc_logic.providers.report_provider import ReportBenchmarkProvider
from calc_logic.providers.rule_provider import RuleBenchmarkProvider
from config import (
    BENCHMARK_PRODUCT_LABELS,
    CATEGORY_LABELS,
    DEFAULT_PENSION_ASSUMPTIONS,
    PRODUCT_BENCHMARK_CATEGORY_MAP,
    REPORT_BENCHMARK_FILE,
)
from economic_context.service import CurrentEconomicContextService
from models.analysis_models import AnalysisBundle, BenchmarkSelection


class AnalysisService:
    def __init__(self):
        self.report_provider = ReportBenchmarkProvider(REPORT_BENCHMARK_FILE)
        self.rule_provider = RuleBenchmarkProvider()
        self.external_benchmark_bridge = MainAnalysisBenchmarkBridge()
        self.economic_context_service = CurrentEconomicContextService()
        self.default_pension_assumptions = DEFAULT_PENSION_ASSUMPTIONS.copy()
        self.metric_provider_map = {
            "household_income": self.report_provider,
            "expense": self.report_provider,
            "debt_payment": self.report_provider,
            "saving_investment": self.report_provider,
            "emergency_fund": self.report_provider,
            "total_assets": self.report_provider,
            "financial_assets_proxy": self.report_provider,
            "real_estate_assets_proxy": self.report_provider,
        }

    @staticmethod
    def _external_reference(value_payload, label: str) -> dict:
        return {
            "label": label,
            "value": float(value_payload.get("value", 0.0)),
            "unit": value_payload.get("unit", ""),
            "source_name": value_payload.get("source_name", ""),
            "period_year": value_payload.get("period_year"),
            "method": value_payload.get("method", ""),
            "detail": value_payload.get("detail", {}),
        }

    def _attach_external_benchmark_details(self, comparisons, external_summary: dict):
        benchmark_values = (external_summary or {}).get("benchmark_context", {}).get("values", {})
        external_analysis = (external_summary or {}).get("analysis", {})
        secondary_map = {
            "household_income": [
                ("peer_monthly_income", "KOSIS 동일 가구 평균소득"),
                ("median_income_reference", "기준중위소득(가구원수 기준)"),
            ],
            "expense": [
                ("peer_monthly_consumption", "KOSIS 동일 가구 월소비지출"),
            ],
            "total_assets": [
                ("peer_total_assets", "KOSIS 동일 가구 총자산"),
            ],
            "financial_assets_proxy": [
                ("peer_financial_assets", "KOSIS 동일 가구 금융자산"),
            ],
            "real_estate_assets_proxy": [
                ("peer_real_estate_assets", "KOSIS 동일 가구 부동산자산"),
            ],
        }
        external_positions = {
            "household_income": external_analysis.get("income_position", {}),
            "expense": external_analysis.get("spending_gap", {}),
            "total_assets": external_analysis.get("asset_position", {}),
            "debt_payment": external_analysis.get("debt_risk_level", {}),
        }

        for metric_name, links in secondary_map.items():
            comparison = comparisons.get(metric_name)
            if comparison is None:
                continue
            references = []
            for benchmark_key, label in links:
                value_payload = benchmark_values.get(benchmark_key)
                if value_payload is None:
                    continue
                references.append(self._external_reference(value_payload, label))
            if references:
                comparison.detail["secondary_benchmarks"] = references
            if external_positions.get(metric_name):
                comparison.detail["external_position"] = external_positions[metric_name]

    def _build_pension_provider(self, profile) -> PensionBenchmarkProvider:
        assumptions = self.default_pension_assumptions.copy()
        assumptions["inflation_rate"] = profile.economic_assumptions.inflation_rate
        assumptions["accumulation_return_rate"] = profile.economic_assumptions.pension_accumulation_return_rate
        assumptions["payout_return_rate"] = profile.economic_assumptions.pension_payout_return_rate
        return PensionBenchmarkProvider(assumptions)

    def analyze(self, profile, warnings=None) -> AnalysisBundle:
        warnings = warnings or []
        selection_payload = self.report_provider.select_group_and_band(profile)
        selection = BenchmarkSelection(
            group_id=selection_payload["group_id"],
            group_title=selection_payload["group_title"],
            band_key=selection_payload["band_key"],
            band_income=float(selection_payload["band"]["household_income"]),
            fallback_note=selection_payload["fallback_note"],
            band_min_income=selection_payload["band_rule"].get("min"),
            band_max_income=selection_payload["band_rule"].get("max"),
            selection_method=selection_payload["selection_method"],
            detail={"selection_method": selection_payload["selection_method"]},
        )

        metric_pairs = {
            "household_income": profile.household_income,
            "expense": profile.monthly_expense,
            "debt_payment": profile.monthly_debt_payment,
            "saving_investment": profile.monthly_saving_investment,
            "emergency_fund": profile.monthly_emergency_fund,
            "total_assets": profile.total_assets,
            "financial_assets_proxy": profile.liquid_assets,
            "real_estate_assets_proxy": profile.non_liquid_assets,
        }

        comparisons = {}
        for metric_name, actual_value in metric_pairs.items():
            provider = self.metric_provider_map[metric_name]
            benchmark_info = provider.get_metric(metric_name, selection_payload, profile)
            reverse = metric_name == "debt_payment"
            comparisons[metric_name] = compare_metric(
                metric_name=metric_name,
                label=benchmark_info["label"],
                actual_value=actual_value,
                benchmark_info=benchmark_info,
                reverse=reverse,
            )

        category_payload = self.report_provider.get_expense_categories(selection_payload)
        category_comparisons = build_category_comparisons(
            actual_categories=profile.expense_categories,
            benchmark_payload=category_payload,
            category_labels=CATEGORY_LABELS,
        )
        income_allocation_payload = self.report_provider.get_income_allocation(selection_payload)
        income_allocation_comparisons = build_income_allocation_comparisons(
            profile,
            income_allocation_payload,
        )
        dominant_expense_payload = self.report_provider.get_dominant_expense_category(selection_payload)
        dominant_expense_analysis = build_dominant_expense_analysis(
            profile,
            dominant_expense_payload,
        )

        pension_provider = self._build_pension_provider(profile)
        pension_result = pension_provider.calculate_required_monthly_contribution(profile.pension)
        emergency_rule_result = self.rule_provider.get_emergency_fund_target(profile)
        saving_product_payload = self.report_provider.get_saving_product_benchmark(selection_payload)
        tax_benefit_payload = self.report_provider.get_tax_benefit_rules()
        saving_product_analysis = analyze_saving_products(
            actual_products=profile.saving_products,
            monthly_saving_investment=profile.monthly_saving_investment,
            benchmark_payload=saving_product_payload,
            benchmark_product_labels=BENCHMARK_PRODUCT_LABELS,
            product_category_map=PRODUCT_BENCHMARK_CATEGORY_MAP,
            tax_benefit_payload=tax_benefit_payload,
        )
        external_benchmark_summary = self.external_benchmark_bridge.analyze_profile(profile)
        self._attach_external_benchmark_details(comparisons, external_benchmark_summary)
        economic_context_summary = self.economic_context_service.build_context_summary(profile.economic_assumptions)
        home_purchase_result = calculate_home_purchase_plan(
            house_price=profile.home_purchase_goal.house_price,
            ltv=profile.home_purchase_goal.ltv,
            dti=profile.home_purchase_goal.dti,
            target_years=profile.home_purchase_goal.target_years,
            loan_term_years=profile.home_purchase_goal.loan_term_years,
            loan_interest_rate=profile.home_purchase_goal.loan_interest_rate,
            household_income=profile.household_income,
        )

        return AnalysisBundle(
            benchmark_selection=selection,
            warnings=warnings,
            metric_comparisons=comparisons,
            category_comparisons=category_comparisons,
            pension_result=pension_result,
            emergency_rule_result=emergency_rule_result,
            saving_product_analysis=saving_product_analysis,
            home_purchase_result=home_purchase_result,
            raw_context={
                "household_income": profile.household_income,
                "monthly_surplus": profile.monthly_surplus,
                "monthly_outflow": profile.total_monthly_outflow,
                "economic_assumptions": asdict(profile.economic_assumptions),
                "special_goals": [asdict(goal) for goal in profile.special_goals],
                "total_special_goal_amount": profile.total_special_goal_amount,
                "insurance_products": profile.insurance_products,
                "total_insurance_premium": profile.total_insurance_premium,
                "home_purchase_goal": asdict(profile.home_purchase_goal),
                "income_allocation": {
                    key: asdict(value) for key, value in income_allocation_comparisons.items()
                },
                "dominant_expense_analysis": asdict(dominant_expense_analysis),
                "external_benchmark_summary": external_benchmark_summary,
                "economic_context_summary": economic_context_summary,
            },
            income_allocation_comparisons=income_allocation_comparisons,
            dominant_expense_analysis=dominant_expense_analysis,
            external_benchmark_summary=external_benchmark_summary,
            economic_context_summary=economic_context_summary,
        )
