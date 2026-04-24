from typing import Iterable, List, Optional


def calculate_required_monthly_saving(target_amount: float, annual_rate: float, years: int) -> float:
    safe_target_amount = max(float(target_amount or 0.0), 0.0)
    safe_years = max(int(years or 0), 0)
    safe_annual_rate = max(float(annual_rate or 0.0), 0.0)

    months = safe_years * 12
    if safe_target_amount <= 0 or months <= 0:
        return 0.0

    monthly_rate = safe_annual_rate / 12.0
    if abs(monthly_rate) < 1e-9:
        return safe_target_amount / months

    factor = ((1.0 + monthly_rate) ** months) - 1.0
    if abs(factor) < 1e-9:
        return safe_target_amount / months
    return safe_target_amount * monthly_rate / factor


def build_special_goal_saving_plan(
    goals: Iterable[dict],
    installment_return_rate: float,
    investment_return_rate: float,
    default_target_years: int = 0,
    excluded_names: Optional[Iterable[str]] = None,
) -> List[dict]:
    excluded = {str(name).strip() for name in (excluded_names or []) if str(name).strip()}
    rows: List[dict] = []

    for goal in goals or []:
        name = str((goal or {}).get("name", "")).strip()
        target_amount = float((goal or {}).get("target_amount", 0.0) or 0.0)
        target_years = int((goal or {}).get("target_years", default_target_years) or default_target_years or 0)
        if not name or name in excluded:
            continue

        rows.append(
            {
                "name": name,
                "target_amount": target_amount,
                "target_years": max(int(target_years or 0), 0),
                "installment_monthly_saving": calculate_required_monthly_saving(
                    target_amount=target_amount,
                    annual_rate=installment_return_rate,
                    years=target_years,
                ),
                "investment_monthly_saving": calculate_required_monthly_saving(
                    target_amount=target_amount,
                    annual_rate=investment_return_rate,
                    years=target_years,
                ),
            }
        )

    return rows
