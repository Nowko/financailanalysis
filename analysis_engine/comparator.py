from analysis_engine.models import AnalysisResult


def _safe_ratio(actual: float, benchmark: float) -> float:
    if not benchmark:
        return 0.0
    return actual / benchmark


def _classify_ratio(ratio: float) -> str:
    if ratio >= 1.2:
        return "above"
    if ratio >= 0.9:
        return "near"
    return "below"


class HouseholdAnalysisEngine:
    def __init__(self, benchmark_provider):
        self.benchmark_provider = benchmark_provider

    def analyze(self, household_input) -> tuple:
        benchmark_context = self.benchmark_provider.provide(household_input)
        values = benchmark_context.values

        median_income = values.get("median_income_reference")
        peer_income = values.get("peer_monthly_income")
        peer_assets = values.get("peer_total_assets")
        peer_debt = values.get("peer_total_debt")
        peer_spending = values.get("peer_monthly_consumption")

        income_position = {
            "monthly_income": household_input.monthly_income,
            "median_income_reference": median_income.value if median_income else None,
            "peer_income_reference": peer_income.value if peer_income else None,
            "vs_median_income_ratio": _safe_ratio(
                household_input.monthly_income,
                median_income.value if median_income else 0.0,
            ),
            "vs_peer_income_ratio": _safe_ratio(
                household_input.monthly_income,
                peer_income.value if peer_income else 0.0,
            ),
        }
        income_position["level"] = _classify_ratio(
            income_position["vs_peer_income_ratio"] or income_position["vs_median_income_ratio"]
        )

        asset_position = {
            "total_assets": household_input.total_assets,
            "financial_assets": household_input.financial_assets,
            "real_estate_assets": household_input.real_estate_assets,
            "peer_total_assets_reference": peer_assets.value if peer_assets else None,
            "vs_peer_total_assets_ratio": _safe_ratio(
                household_input.total_assets,
                peer_assets.value if peer_assets else 0.0,
            ),
        }
        asset_position["level"] = _classify_ratio(asset_position["vs_peer_total_assets_ratio"])

        debt_ratio_to_assets = _safe_ratio(household_input.total_debt, household_input.total_assets)
        debt_ratio_to_peer = _safe_ratio(
            household_input.total_debt,
            peer_debt.value if peer_debt else 0.0,
        )
        debt_to_annual_income_ratio = _safe_ratio(
            household_input.total_debt,
            household_input.monthly_income * 12,
        )
        debt_risk = "low"
        if (
            debt_ratio_to_assets >= 0.35
            or debt_ratio_to_peer >= 1.2
            or debt_to_annual_income_ratio >= 2.5
        ):
            debt_risk = "high"
        elif (
            debt_ratio_to_assets >= 0.20
            or debt_ratio_to_peer >= 0.85
            or debt_to_annual_income_ratio >= 1.0
        ):
            debt_risk = "moderate"
        debt_risk_level = {
            "total_debt": household_input.total_debt,
            "peer_total_debt_reference": peer_debt.value if peer_debt else None,
            "debt_to_assets_ratio": debt_ratio_to_assets,
            "vs_peer_debt_ratio": debt_ratio_to_peer,
            "debt_to_annual_income_ratio": debt_to_annual_income_ratio,
            "level": debt_risk,
        }

        spending_gap = {
            "monthly_consumption": household_input.monthly_consumption,
            "peer_monthly_consumption_reference": peer_spending.value if peer_spending else None,
            "vs_peer_consumption_ratio": _safe_ratio(
                household_input.monthly_consumption,
                peer_spending.value if peer_spending else 0.0,
            ),
            "gap": household_input.monthly_consumption - (peer_spending.value if peer_spending else 0.0),
        }
        spending_gap["level"] = _classify_ratio(spending_gap["vs_peer_consumption_ratio"])

        household_profile_summary = {
            "household_size": household_input.household_size,
            "reference_age": household_input.reference_age,
            "age_band": household_input.age_band,
            "monthly_surplus": household_input.monthly_surplus,
            "asset_to_debt_ratio": _safe_ratio(household_input.total_assets, household_input.total_debt),
        }

        analysis_result = AnalysisResult(
            income_position=income_position,
            asset_position=asset_position,
            debt_risk_level=debt_risk_level,
            spending_gap=spending_gap,
            household_profile_summary=household_profile_summary,
            benchmark_trace=benchmark_context.to_dict(),
            notes=list(household_input.warnings) + list(benchmark_context.notes),
        )
        return benchmark_context, analysis_result
