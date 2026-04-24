from models.analysis_models import MetricComparison


def classify_gap(gap_rate: float, reverse: bool = False) -> str:
    score = -gap_rate if reverse else gap_rate
    if score <= -0.10:
        return "부족"
    if score >= 0.10:
        return "상회"
    return "유사"


def compare_metric(metric_name: str, label: str, actual_value: float, benchmark_info: dict, reverse: bool = False) -> MetricComparison:
    benchmark_value = float(benchmark_info["value"])
    gap = actual_value - benchmark_value
    gap_rate = 0.0 if benchmark_value == 0 else gap / benchmark_value
    status = classify_gap(gap_rate, reverse=reverse)

    return MetricComparison(
        metric_name=metric_name,
        label=label,
        actual_value=float(actual_value),
        benchmark_value=benchmark_value,
        gap=gap,
        gap_rate=gap_rate,
        status=status,
        source=benchmark_info["source"],
        method=benchmark_info.get("method", ""),
        detail=benchmark_info.get("detail", {}),
    )
