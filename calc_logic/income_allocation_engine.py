from typing import Dict

from config import CATEGORY_LABELS
from models.analysis_models import DominantExpenseAnalysis, IncomeAllocationComparison


def _safe_ratio(amount: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return float(amount) / float(total)


def _classify_ratio_gap(ratio_gap_rate: float) -> str:
    if ratio_gap_rate <= -0.10:
        return "낮음"
    if ratio_gap_rate >= 0.10:
        return "높음"
    return "유사"


def build_income_allocation_comparisons(profile, benchmark_payload: dict) -> Dict[str, IncomeAllocationComparison]:
    source = benchmark_payload.get("source", "")
    method = benchmark_payload.get("method", "")
    common_detail = benchmark_payload.get("detail", {})
    flows = benchmark_payload.get("flows", {})

    actual_amounts = {
        "expense": float(profile.monthly_expense),
        "debt_payment": float(profile.monthly_debt_payment),
        "saving_investment": float(profile.monthly_saving_investment),
        "emergency_fund": float(profile.monthly_emergency_fund),
    }

    comparisons: Dict[str, IncomeAllocationComparison] = {}
    for flow_key, actual_amount in actual_amounts.items():
        flow_info = flows.get(flow_key, {})
        benchmark_amount = float(flow_info.get("amount", 0.0))
        benchmark_ratio = float(flow_info.get("ratio", 0.0))
        actual_ratio = _safe_ratio(actual_amount, float(profile.household_income))
        amount_gap = actual_amount - benchmark_amount
        ratio_gap = actual_ratio - benchmark_ratio
        ratio_gap_rate = 0.0 if benchmark_ratio == 0 else ratio_gap / benchmark_ratio

        comparisons[flow_key] = IncomeAllocationComparison(
            flow_key=flow_key,
            label=flow_info.get("label", flow_key),
            actual_amount=actual_amount,
            benchmark_amount=benchmark_amount,
            actual_ratio=actual_ratio,
            benchmark_ratio=benchmark_ratio,
            amount_gap=amount_gap,
            ratio_gap=ratio_gap,
            ratio_gap_rate=ratio_gap_rate,
            status=_classify_ratio_gap(ratio_gap_rate),
            source=source,
            method=method,
            detail={**common_detail, "flow_key": flow_key},
        )
    return comparisons


def build_dominant_expense_analysis(profile, benchmark_payload: dict) -> DominantExpenseAnalysis:
    source = benchmark_payload.get("source", "")
    method = benchmark_payload.get("method", "")
    common_detail = benchmark_payload.get("detail", {})
    dominant_key = benchmark_payload.get("category_key", "")
    dominant_label = benchmark_payload.get("label") or CATEGORY_LABELS.get(dominant_key, dominant_key)
    benchmark_amount = float(benchmark_payload.get("amount", 0.0))
    benchmark_fixed_spend_rate = benchmark_payload.get("fixed_spend_rate")
    actual_amount = float(profile.expense_categories.get(dominant_key, 0.0))
    actual_gap = actual_amount - benchmark_amount
    actual_gap_rate = 0.0 if benchmark_amount == 0 else actual_gap / benchmark_amount

    actual_categories = {key: float(value) for key, value in profile.expense_categories.items()}
    if actual_categories:
        actual_top_key, actual_top_amount = max(actual_categories.items(), key=lambda item: item[1])
    else:
        actual_top_key, actual_top_amount = "", 0.0
    actual_top_label = CATEGORY_LABELS.get(actual_top_key, actual_top_key)

    return DominantExpenseAnalysis(
        category_key=dominant_key,
        label=dominant_label,
        benchmark_amount=benchmark_amount,
        benchmark_fixed_spend_rate=benchmark_fixed_spend_rate,
        actual_amount=actual_amount,
        actual_gap=actual_gap,
        actual_gap_rate=actual_gap_rate,
        actual_top_category_key=actual_top_key,
        actual_top_label=actual_top_label,
        actual_top_amount=actual_top_amount,
        matches_actual_top=actual_top_key == dominant_key,
        source=source,
        method=method,
        detail=common_detail,
    )
