import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from calc_logic.economic_assumption_registry import DEFAULT_ECONOMIC_ASSUMPTIONS
from economic_context.models import CurrentEconomicContext, CurrentEconomicMetric


CURRENT_ECONOMIC_CONTEXT_FILE = (
    Path(__file__).resolve().parents[1] / "data" / "current_context" / "current_economic_context.json"
)


def _round_rate(value: float) -> float:
    return round(float(value), 4)


@lru_cache(maxsize=4)
def _load_context_from_path(path_str: str) -> CurrentEconomicContext:
    with open(path_str, "r", encoding="utf-8") as file:
        payload = json.load(file)

    metrics = {}
    for key, item in payload.get("metrics", {}).items():
        metrics[key] = CurrentEconomicMetric(
            key=key,
            label=item["label"],
            value=float(item["value"]),
            unit=item.get("unit", "rate"),
            as_of_date=item.get("as_of_date", ""),
            published_at=item.get("published_at", ""),
            source_name=item.get("source_name", ""),
            official_url=item.get("official_url", ""),
            method=item.get("method", ""),
            note=item.get("note", ""),
        )

    return CurrentEconomicContext(
        context_name=payload.get("context_name", "current_context"),
        as_of_date=payload.get("as_of_date", ""),
        metrics=metrics,
        notes=list(payload.get("notes", [])),
        assumption_policy=dict(payload.get("assumption_policy", {})),
    )


class CurrentEconomicContextService:
    def __init__(self, data_path: Path = None):
        self.data_path = Path(data_path or CURRENT_ECONOMIC_CONTEXT_FILE)

    def load_context(self) -> CurrentEconomicContext:
        return _load_context_from_path(str(self.data_path))

    def _metric_value(self, context: CurrentEconomicContext, key: str, fallback_key: str = "") -> float:
        metric = context.metrics.get(key)
        if metric is not None:
            return float(metric.value)
        if fallback_key:
            return float(DEFAULT_ECONOMIC_ASSUMPTIONS[fallback_key])
        return 0.0

    def get_recommended_assumptions(self) -> Dict[str, float]:
        context = self.load_context()
        inflation_rate = self._metric_value(context, "cpi_yoy", "inflation_rate")
        installment_return_rate = self._metric_value(context, "deposit_rate_avg", "installment_return_rate")
        treasury_3y_yield = self._metric_value(context, "treasury_3y_yield", "investment_return_rate")
        base_rate = self._metric_value(context, "base_rate", "pension_payout_return_rate")

        investment_return_rate = max(installment_return_rate + 0.005, treasury_3y_yield)
        pension_accumulation_return_rate = investment_return_rate
        pension_payout_return_rate = max(inflation_rate, min(base_rate, installment_return_rate))

        return {
            "inflation_rate": _round_rate(inflation_rate),
            "investment_return_rate": _round_rate(investment_return_rate),
            "installment_return_rate": _round_rate(installment_return_rate),
            "pension_accumulation_return_rate": _round_rate(pension_accumulation_return_rate),
            "pension_payout_return_rate": _round_rate(pension_payout_return_rate),
        }

    def build_context_summary(self, applied_assumptions=None) -> dict:
        context = self.load_context()
        recommended = self.get_recommended_assumptions()
        applied_assumptions = applied_assumptions or recommended

        assumption_entries = []
        for key, recommended_value in recommended.items():
            if isinstance(applied_assumptions, dict):
                applied_raw_value = applied_assumptions.get(key, recommended_value)
            else:
                applied_raw_value = getattr(applied_assumptions, key, recommended_value)
            applied_value = float(applied_raw_value)
            policy = context.assumption_policy.get(key, {})
            assumption_entries.append(
                {
                    "key": key,
                    "recommended_value": recommended_value,
                    "applied_value": applied_value,
                    "is_recommended_applied": abs(applied_value - recommended_value) < 1e-9,
                    "rule": policy.get("rule", ""),
                    "description": policy.get("description", ""),
                    "source_metrics": list(policy.get("source_metrics", [])),
                }
            )

        return {
            "context_name": context.context_name,
            "as_of_date": context.as_of_date,
            "metrics": {key: metric.to_dict() for key, metric in context.metrics.items()},
            "notes": list(context.notes),
            "recommended_assumptions": recommended,
            "applied_assumptions": {
                entry["key"]: entry["applied_value"] for entry in assumption_entries
            },
            "assumption_entries": assumption_entries,
        }

    def build_default_percent_map(self) -> Dict[str, float]:
        return {
            key: value * 100.0
            for key, value in self.get_recommended_assumptions().items()
        }

    def build_ui_hint(self) -> str:
        context = self.load_context()
        metrics = context.metrics
        base_rate = metrics.get("base_rate")
        cpi = metrics.get("cpi_yoy")
        deposit = metrics.get("deposit_rate_avg")
        treasury = metrics.get("treasury_3y_yield")

        parts = [f"기준일 {context.as_of_date}"]
        if cpi:
            parts.append(f"물가 {cpi.value * 100:.1f}%")
        if deposit:
            parts.append(f"예금 {deposit.value * 100:.2f}%")
        if treasury:
            parts.append(f"국고채3년 {treasury.value * 100:.2f}%")
        if base_rate:
            parts.append(f"기준금리 {base_rate.value * 100:.2f}%")
        return " / ".join(parts)
