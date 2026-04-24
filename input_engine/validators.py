from typing import Dict

from input_engine.schemas import HouseholdInput


def _to_int(value, field_name: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{field_name} is required.")
    return int(float(str(value).replace(",", "").strip()))


def _to_float(value, field_name: str, default: float = 0.0) -> float:
    if value is None or str(value).strip() == "":
        return float(default)
    return float(str(value).replace(",", "").strip())


def _age_band(reference_age: int) -> str:
    if reference_age < 20:
        return "under_20"
    if reference_age < 30:
        return "20s"
    if reference_age < 40:
        return "30s"
    if reference_age < 50:
        return "40s"
    if reference_age < 60:
        return "50s"
    return "60plus"


def parse_household_input(payload: Dict[str, object]) -> HouseholdInput:
    household_size = _to_int(payload.get("household_size"), "household_size")
    reference_age = _to_int(payload.get("reference_age"), "reference_age")
    age_band = str(payload.get("age_band", "")).strip() or _age_band(reference_age)
    monthly_income = _to_float(payload.get("monthly_income"), "monthly_income")
    disposable_income = _to_float(
        payload.get("disposable_income"),
        "disposable_income",
        default=monthly_income,
    )
    total_assets = _to_float(payload.get("total_assets"), "total_assets")
    financial_assets = _to_float(payload.get("financial_assets"), "financial_assets")
    real_estate_assets = _to_float(payload.get("real_estate_assets"), "real_estate_assets")
    total_debt = _to_float(payload.get("total_debt"), "total_debt")
    monthly_consumption = _to_float(payload.get("monthly_consumption"), "monthly_consumption")

    if household_size <= 0:
        raise ValueError("household_size must be at least 1.")
    if reference_age <= 0:
        raise ValueError("reference_age must be positive.")

    warnings = []
    if disposable_income <= 0:
        warnings.append("Disposable income was missing or zero; monthly income was used as a fallback.")
        disposable_income = monthly_income
    if total_assets < financial_assets + real_estate_assets:
        warnings.append("total_assets is lower than the sum of financial_assets and real_estate_assets.")

    return HouseholdInput(
        household_size=household_size,
        reference_age=reference_age,
        age_band=age_band,
        monthly_income=monthly_income,
        disposable_income=disposable_income,
        total_assets=total_assets,
        financial_assets=financial_assets,
        real_estate_assets=real_estate_assets,
        total_debt=total_debt,
        monthly_consumption=monthly_consumption,
        pension_monthly_contribution=_to_float(
            payload.get("pension_monthly_contribution"),
            "pension_monthly_contribution",
        ),
        pension_current_age=(
            _to_int(payload.get("pension_current_age"), "pension_current_age")
            if payload.get("pension_current_age") not in ("", None)
            else None
        ),
        pension_retirement_age=(
            _to_int(payload.get("pension_retirement_age"), "pension_retirement_age")
            if payload.get("pension_retirement_age") not in ("", None)
            else None
        ),
        pension_target_monthly_amount=(
            _to_float(payload.get("pension_target_monthly_amount"), "pension_target_monthly_amount")
            if payload.get("pension_target_monthly_amount") not in ("", None)
            else None
        ),
        metadata=dict(payload.get("metadata", {})),
        warnings=warnings,
    )
