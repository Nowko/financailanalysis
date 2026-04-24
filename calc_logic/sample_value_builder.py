from typing import Dict, Iterable


GENERAL_PRODUCT_KEYS = ("cash_flow", "installment", "investment")
INSURANCE_PRODUCT_KEYS = (
    "indemnity_insurance",
    "life_insurance",
    "variable_insurance",
)


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _monthly_amount_from_annual_cap(annual_cap: float) -> float:
    return round(_safe_float(annual_cap) / 12.0, 2)


def _allocate_integer_amounts(ratios: Dict[str, float], total_amount: float) -> Dict[str, float]:
    target_total = max(int(round(_safe_float(total_amount, 0.0))), 0)
    keys = list(ratios.keys())
    if target_total <= 0 or not keys:
        return {key: 0.0 for key in keys}

    ratio_sum = sum(max(_safe_float(value, 0.0), 0.0) for value in ratios.values())
    if ratio_sum <= 0:
        ratio_sum = float(len(keys))
        normalized_ratios = {key: 1.0 / len(keys) for key in keys}
    else:
        normalized_ratios = {key: max(_safe_float(value, 0.0), 0.0) / ratio_sum for key, value in ratios.items()}

    raw_allocations = {key: normalized_ratios[key] * target_total for key in keys}
    floored_allocations = {key: int(raw_allocations[key]) for key in keys}
    remainder = target_total - sum(floored_allocations.values())

    if remainder > 0:
        fractional_order = sorted(
            keys,
            key=lambda key: raw_allocations[key] - floored_allocations[key],
            reverse=True,
        )
        for key in fractional_order[:remainder]:
            floored_allocations[key] += 1

    return {key: float(value) for key, value in floored_allocations.items()}


def build_tax_benefit_sample(tax_benefit_payload: Dict[str, object]) -> Dict[str, float]:
    products = (tax_benefit_payload or {}).get("products", {})
    pension_info = products.get("pension_savings", {})
    irp_info = products.get("irp", {})
    housing_info = products.get("housing_subscription", {})

    pension_monthly = _monthly_amount_from_annual_cap(pension_info.get("annual_cap", 0))
    combined_pension_monthly = _monthly_amount_from_annual_cap(
        pension_info.get("combined_cap", irp_info.get("combined_cap", irp_info.get("annual_cap", 0)))
    )
    irp_monthly = max(round(combined_pension_monthly - pension_monthly, 2), 0.0)
    housing_monthly = _monthly_amount_from_annual_cap(housing_info.get("annual_cap", 0))

    return {
        "pension_savings": pension_monthly,
        "irp": irp_monthly,
        "housing_subscription": housing_monthly,
    }


def build_general_product_sample(benchmark_payload: Dict[str, object], total_amount: float) -> Dict[str, float]:
    products = (benchmark_payload or {}).get("products", {})
    ratios = {
        key: _safe_float(products.get(key, {}).get("ratio"), 0.0)
        for key in GENERAL_PRODUCT_KEYS
    }
    return _allocate_integer_amounts(ratios, total_amount)


def build_insurance_sample(total_amount: float = 3.0) -> Dict[str, float]:
    return _allocate_integer_amounts({key: 1.0 for key in INSURANCE_PRODUCT_KEYS}, total_amount)


def merge_product_samples(*sample_maps: Iterable[Dict[str, float]]) -> Dict[str, float]:
    merged: Dict[str, float] = {}
    for sample_map in sample_maps:
        for key, value in sample_map.items():
            merged[key] = round(_safe_float(value, 0.0), 2)
    return merged


def build_reference_sample_values(report_provider, profile_like, insurance_total: float = 3.0) -> Dict[str, object]:
    selection = report_provider.select_group_and_band(profile_like)
    band = selection["band"]
    expense_payload = report_provider.get_expense_categories(selection)
    benchmark_payload = report_provider.get_saving_product_benchmark(selection)
    tax_benefit_payload = report_provider.get_tax_benefit_rules()

    tax_benefit_sample = build_tax_benefit_sample(tax_benefit_payload)
    insurance_sample = build_insurance_sample(insurance_total)
    monthly_saving_target = _safe_float(
        getattr(profile_like, "monthly_saving_investment", 0.0),
        _safe_float(band.get("saving_investment"), 0.0),
    )
    reserved_amount = sum(tax_benefit_sample.values()) + sum(insurance_sample.values())
    if monthly_saving_target < reserved_amount:
        monthly_saving_target = reserved_amount
    general_sample = build_general_product_sample(
        benchmark_payload,
        monthly_saving_target - reserved_amount,
    )

    return {
        "selection": selection,
        "financial_fields": {
            "household_income": _safe_float(band.get("household_income"), 0.0),
            "monthly_expense": _safe_float(band.get("expense"), 0.0),
            "monthly_debt_payment": _safe_float(band.get("debt_payment"), 0.0),
            "monthly_saving_investment": round(monthly_saving_target, 2),
            "monthly_emergency_fund": max(_safe_float(band.get("emergency_fund"), 0.0), 0.0),
            "average_consumption": _safe_float(band.get("expense"), 0.0),
            "liquid_assets": _safe_float(band.get("financial_assets"), 0.0),
            "non_liquid_assets": _safe_float(band.get("real_estate_assets"), 0.0),
        },
        "expense_categories": {
            key: _safe_float(value, 0.0)
            for key, value in expense_payload.get("values", {}).items()
        },
        "saving_products": merge_product_samples(general_sample, tax_benefit_sample),
        "insurance_products": insurance_sample,
    }
