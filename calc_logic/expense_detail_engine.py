from typing import Dict

from models.analysis_models import CategoryComparison


def classify_category_gap(gap_rate: float) -> str:
    if gap_rate <= -0.15:
        return "낮음"
    if gap_rate >= 0.15:
        return "높음"
    return "유사"


def build_category_comparisons(actual_categories: Dict[str, float], benchmark_payload: dict, category_labels: Dict[str, str]) -> Dict[str, CategoryComparison]:
    benchmark_values = benchmark_payload.get("values", {})
    fixed_rates = benchmark_payload.get("fixed_rates", {})
    source = benchmark_payload.get("source", "")
    method = benchmark_payload.get("method", "")
    common_detail = benchmark_payload.get("detail", {})
    result: Dict[str, CategoryComparison] = {}

    for key, label in category_labels.items():
        actual_value = float(actual_categories.get(key, 0.0))
        benchmark_value = float(benchmark_values.get(key, 0.0))
        gap = actual_value - benchmark_value
        gap_rate = 0.0 if benchmark_value == 0 else gap / benchmark_value
        result[key] = CategoryComparison(
            category_key=key,
            label=label,
            actual_value=actual_value,
            benchmark_value=benchmark_value,
            gap=gap,
            gap_rate=gap_rate,
            status=classify_category_gap(gap_rate),
            fixed_spend_rate=fixed_rates.get(key),
            source=source,
            method=method,
            detail={**common_detail, "category_key": key},
        )
    return result
