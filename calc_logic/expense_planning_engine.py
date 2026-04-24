from typing import Dict, Iterable, Mapping, Optional, Sequence


def sum_detail_values(
    detail_values: Mapping[str, float],
    multipliers: Optional[Mapping[str, float]] = None,
) -> float:
    return sum(
        float(value or 0.0) * float((multipliers or {}).get(key, 1.0) or 1.0)
        for key, value in (detail_values or {}).items()
    )


def has_detail_values(detail_values: Mapping[str, float]) -> bool:
    return any(abs(float(value or 0.0)) > 1e-9 for value in (detail_values or {}).values())


def resolve_category_total(
    manual_total: float,
    detail_values: Mapping[str, float],
    multipliers: Optional[Mapping[str, float]] = None,
) -> float:
    if has_detail_values(detail_values):
        return sum_detail_values(detail_values, multipliers=multipliers)
    return float(manual_total or 0.0)


def build_allocation_summary_rows(
    saving_products: Mapping[str, float],
    insurance_products: Mapping[str, float],
    labels: Mapping[str, str],
    ordered_keys: Sequence[str],
) -> Iterable[Dict[str, float]]:
    rows = []
    for key in ordered_keys:
        if key in (insurance_products or {}):
            amount = float((insurance_products or {}).get(key, 0.0) or 0.0)
        else:
            amount = float((saving_products or {}).get(key, 0.0) or 0.0)
        rows.append({"key": key, "label": labels.get(key, key), "amount": amount})
    return rows


def calculate_expense_plan_summary(
    category_totals: Mapping[str, float],
    household_income: float,
    saving_products: Mapping[str, float],
    insurance_products: Mapping[str, float],
    labels: Mapping[str, str],
    ordered_keys: Sequence[str],
) -> Dict[str, object]:
    expense_total = sum(float(value or 0.0) for value in (category_totals or {}).values())
    available_cash = float(household_income or 0.0) - expense_total
    allocation_rows = list(build_allocation_summary_rows(saving_products, insurance_products, labels, ordered_keys))
    allocation_total = sum(row["amount"] for row in allocation_rows)
    allocation_gap = available_cash - allocation_total

    return {
        "expense_total": expense_total,
        "available_cash": available_cash,
        "allocation_rows": allocation_rows,
        "allocation_total": allocation_total,
        "allocation_gap": allocation_gap,
    }
