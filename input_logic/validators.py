from datetime import date
from typing import Dict, List, Optional, Tuple

from config import (
    CATEGORY_LABELS,
    DEFAULT_ECONOMIC_ASSUMPTIONS,
    DEFAULT_HOME_PURCHASE_GOAL,
    INSURANCE_PRODUCT_LABELS,
    PRODUCT_INPUT_GROUPS,
    PRODUCT_LABELS,
)
from economic_context.service import CurrentEconomicContextService
from housing_context.service import CurrentHomeLoanContextService


EXPENSE_CATEGORY_LABELS = CATEGORY_LABELS
SAVING_PRODUCT_LABELS = PRODUCT_LABELS

ECONOMIC_ASSUMPTION_LABELS = {
    "inflation_rate": "물가상승률",
    "investment_return_rate": "투자 수익률",
    "installment_return_rate": "적금 수익률",
    "pension_accumulation_return_rate": "연금 적립 수익률",
    "pension_payout_return_rate": "연금 수령 수익률",
}

HOME_PURCHASE_LABELS = {
    "house_price": "집 값",
    "ltv": "LTV",
    "dti": "DTI",
    "target_years": "목표 기간",
    "loan_term_years": "대출 기간",
    "loan_interest_rate": "대출 이자율",
}


def _clean_numeric_text(value) -> str:
    return str(value).replace(",", "").strip()


def _parse_optional_number(value, field_name: str, errors: List[str]) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(_clean_numeric_text(value))
    except ValueError:
        errors.append(f"{field_name} 값은 숫자여야 합니다.")
        return None


def _to_number(value, field_name: str, errors: List[str], allow_blank: bool = False, default: float = 0.0) -> float:
    if value is None or str(value).strip() == "":
        if allow_blank:
            return float(default)
        errors.append(f"{field_name} 값이 비어 있습니다.")
        return float(default)

    parsed = _parse_optional_number(value, field_name, errors)
    if parsed is None:
        return float(default)
    return parsed


def _safe_int(value: Optional[float]) -> int:
    if value is None:
        return 0
    return int(value)


def _derive_age_from_birth_parts(birth_year: int, birth_month: int, birth_day: int, today: date) -> int:
    age = today.year - birth_year
    if birth_month > 0 and birth_day > 0 and (today.month, today.day) < (birth_month, birth_day):
        age -= 1
    return age


def _derive_birth_year_from_age(age: int, birth_month: int, birth_day: int, today: date) -> int:
    birth_year = today.year - age
    if birth_month > 0 and birth_day > 0 and (birth_month, birth_day) > (today.month, today.day):
        birth_year -= 1
    return birth_year


def _normalize_economic_assumptions(raw: Dict[str, object], errors: List[str]) -> Dict[str, float]:
    normalized = {}
    recommended_defaults = CurrentEconomicContextService().get_recommended_assumptions()
    for key, label in ECONOMIC_ASSUMPTION_LABELS.items():
        raw_value = (raw or {}).get(key, "")
        parsed = _parse_optional_number(raw_value, label, errors)
        if parsed is None:
            normalized[key] = recommended_defaults.get(key, DEFAULT_ECONOMIC_ASSUMPTIONS[key])
        else:
            normalized[key] = parsed / 100.0
    return normalized


def _normalize_special_goals(raw: List[dict], errors: List[str], default_target_years: int = 0) -> List[dict]:
    normalized_goals = []
    fallback_target_years = max(int(default_target_years or 0), 0)
    for index, goal in enumerate(raw or [], start=1):
        name = str((goal or {}).get("name", "")).strip()
        amount_value = (goal or {}).get("target_amount", "")
        amount = _parse_optional_number(amount_value, f"목표자금 {index} 금액", errors)

        if not name and amount is None:
            continue
        if not name:
            errors.append(f"목표자금 {index}의 자금명을 입력해 주세요.")
            continue
        if amount is None:
            errors.append(f"목표자금 {index}의 금액을 입력해 주세요.")
            continue
        if amount < 0:
            errors.append(f"목표자금 {index}의 금액은 음수일 수 없습니다.")
            continue

        normalized_goals.append(
            {
                "name": name,
                "target_amount": float(amount),
            }
        )
    return normalized_goals


def _normalize_special_goals(raw: List[dict], errors: List[str], default_target_years: int = 0) -> List[dict]:
    normalized_goals = []
    fallback_target_years = max(int(default_target_years or 0), 0)
    for index, goal in enumerate(raw or [], start=1):
        name = str((goal or {}).get("name", "")).strip()
        amount_value = (goal or {}).get("target_amount", "")
        target_years_value = (goal or {}).get("target_years", "")
        amount = _parse_optional_number(amount_value, f"목표자금 {index} 금액", errors)
        target_years = _parse_optional_number(target_years_value, f"목표자금 {index} 목표기간", errors)

        if not name and amount is None and target_years is None:
            continue
        if not name:
            errors.append(f"목표자금 {index}의 자금명을 입력해 주세요.")
            continue
        if amount is None:
            errors.append(f"목표자금 {index}의 금액을 입력해 주세요.")
            continue
        if target_years is None:
            errors.append(f"목표자금 {index}의 목표기간을 입력해 주세요.")
            continue
        if amount < 0:
            errors.append(f"목표자금 {index}의 금액은 음수일 수 없습니다.")
            continue
        if target_years <= 0:
            errors.append(f"목표자금 {index}의 목표기간은 1년 이상이어야 합니다.")
            continue

        normalized_goals.append(
            {
                "name": name,
                "target_amount": float(amount),
                "target_years": int(target_years),
            }
        )
    return normalized_goals


def _normalize_special_goals(raw: List[dict], errors: List[str], default_target_years: int = 0) -> List[dict]:
    normalized_goals = []
    fallback_target_years = max(int(default_target_years or 0), 0)

    for index, goal in enumerate(raw or [], start=1):
        name = str((goal or {}).get("name", "")).strip()
        amount_value = (goal or {}).get("target_amount", "")
        target_years_value = (goal or {}).get("target_years", "")
        amount = _parse_optional_number(amount_value, f"紐⑺몴?먭툑 {index} 湲덉븸", errors)
        target_years = _parse_optional_number(target_years_value, f"紐⑺몴?먭툑 {index} 紐⑺몴湲곌컙", errors)

        if not name and amount is None and target_years is None:
            continue
        if not name:
            errors.append(f"紐⑺몴?먭툑 {index}???먭툑紐낆쓣 ?낅젰??二쇱꽭??")
            continue
        if amount is None:
            errors.append(f"紐⑺몴?먭툑 {index}??湲덉븸???낅젰??二쇱꽭??")
            continue
        if target_years is None:
            target_years = float(fallback_target_years)
        if amount < 0:
            errors.append(f"紐⑺몴?먭툑 {index}??湲덉븸? ?뚯닔?????놁뒿?덈떎.")
            continue
        if target_years <= 0:
            errors.append(f"紐⑺몴?먭툑 {index}??紐⑺몴湲곌컙? 1???댁긽?댁뼱???⑸땲??")
            continue

        normalized_goals.append(
            {
                "name": name,
                "target_amount": float(amount),
                "target_years": int(target_years),
            }
        )
    return normalized_goals


def _normalize_home_purchase_goal(raw: Dict[str, object], errors: List[str]) -> Dict[str, object]:
    raw = raw or {}
    home_loan_defaults = CurrentHomeLoanContextService().get_recommended_defaults()
    normalized = {
        "house_price": _to_number(
            raw.get("house_price"),
            HOME_PURCHASE_LABELS["house_price"],
            errors,
            allow_blank=True,
            default=home_loan_defaults["house_price"],
        ),
        "ltv": _to_number(
            raw.get("ltv"),
            HOME_PURCHASE_LABELS["ltv"],
            errors,
            allow_blank=True,
            default=home_loan_defaults["ltv"] * 100.0,
        )
        / 100.0,
        "dti": _to_number(
            raw.get("dti"),
            HOME_PURCHASE_LABELS["dti"],
            errors,
            allow_blank=True,
            default=home_loan_defaults["dti"] * 100.0,
        )
        / 100.0,
        "target_years": int(
            _to_number(
                raw.get("target_years"),
                HOME_PURCHASE_LABELS["target_years"],
                errors,
                allow_blank=True,
                default=home_loan_defaults["target_years"],
            )
        ),
        "loan_term_years": int(
            _to_number(
                raw.get("loan_term_years"),
                HOME_PURCHASE_LABELS["loan_term_years"],
                errors,
                allow_blank=True,
                default=home_loan_defaults["loan_term_years"],
            )
        ),
        "loan_interest_rate": _to_number(
            raw.get("loan_interest_rate"),
            HOME_PURCHASE_LABELS["loan_interest_rate"],
            errors,
            allow_blank=True,
            default=home_loan_defaults["loan_interest_rate"] * 100.0,
        )
        / 100.0,
    }

    if normalized["house_price"] < 0:
        errors.append("집 값은 음수일 수 없습니다.")
    if not 0 <= normalized["ltv"] <= 1:
        errors.append("LTV는 0~100% 사이여야 합니다.")
    if not 0 <= normalized["dti"] <= 1:
        errors.append("DTI는 0~100% 사이여야 합니다.")
    if normalized["target_years"] <= 0:
        errors.append("목표 기간은 1년 이상이어야 합니다.")
    if normalized["loan_term_years"] <= 0:
        errors.append("대출 기간은 1년 이상이어야 합니다.")
    if normalized["loan_interest_rate"] < 0:
        errors.append("대출 이자율은 음수일 수 없습니다.")

    return normalized


def validate_raw_input(raw: Dict[str, object]) -> Tuple[Dict[str, object], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    today = date.today()

    birth_year_value = _parse_optional_number(raw.get("birth_year"), "출생년도", errors)
    birth_month_value = _parse_optional_number(raw.get("birth_month"), "출생월", errors)
    birth_day_value = _parse_optional_number(raw.get("birth_day"), "출생일", errors)
    age_value = _parse_optional_number(raw.get("age"), "나이", errors)

    birth_year = _safe_int(birth_year_value)
    birth_month = _safe_int(birth_month_value)
    birth_day = _safe_int(birth_day_value)

    if age_value is None and birth_year_value is None:
        errors.append("출생년도 또는 나이 중 하나는 입력해야 합니다.")
    age = _safe_int(age_value) if age_value is not None else 0

    if birth_year_value is not None and age_value is None:
        age = _derive_age_from_birth_parts(birth_year, birth_month, birth_day, today)
    elif age_value is not None and birth_year_value is None:
        birth_year = _derive_birth_year_from_age(age, birth_month, birth_day, today)
    elif age_value is not None and birth_year_value is not None:
        derived_age = _derive_age_from_birth_parts(birth_year, birth_month, birth_day, today)
        if birth_month > 0 and birth_day > 0 and derived_age != age:
            warnings.append("출생일 기준 나이와 입력 나이가 달라 입력한 나이 값을 우선 사용합니다.")

    marital_status = str(raw.get("marital_status", "single")).strip() or "single"
    youngest_child_stage = str(raw.get("youngest_child_stage", "none")).strip() or "none"
    children_count = int(_to_number(raw.get("children_count"), "자녀 수", errors, allow_blank=True))

    if marital_status == "single":
        children_count = 0
        youngest_child_stage = "none"
    elif children_count <= 0:
        youngest_child_stage = "none"

    normalized_home_purchase_goal = _normalize_home_purchase_goal(raw.get("home_purchase_goal", {}), errors)

    normalized = {
        "name": str(raw.get("name", "")).strip(),
        "gender": str(raw.get("gender", "")).strip(),
        "birth_year": birth_year,
        "birth_month": birth_month,
        "birth_day": birth_day,
        "age": age,
        "marital_status": marital_status,
        "children_count": children_count,
        "youngest_child_stage": youngest_child_stage,
        "household_income": _to_number(raw.get("household_income"), "월 가구소득", errors),
        "monthly_expense": _to_number(raw.get("monthly_expense"), "월 소비/지출", errors),
        "monthly_debt_payment": _to_number(raw.get("monthly_debt_payment"), "월 부채상환", errors, allow_blank=True),
        "monthly_saving_investment": _to_number(raw.get("monthly_saving_investment"), "월 저축/투자", errors, allow_blank=True),
        "monthly_emergency_fund": _to_number(raw.get("monthly_emergency_fund"), "월 예비자금", errors, allow_blank=True),
        "average_consumption": _to_number(raw.get("average_consumption"), "평균 소비액", errors, allow_blank=True),
        "liquid_assets": _to_number(raw.get("liquid_assets"), "계좌 현금성 자산", errors, allow_blank=True),
        "non_liquid_assets": _to_number(raw.get("non_liquid_assets"), "비현금성 보유자산", errors, allow_blank=True),
        "economic_assumptions": _normalize_economic_assumptions(raw.get("economic_assumptions", {}), errors),
        "special_goals": _normalize_special_goals(
            raw.get("special_goals", []),
            errors,
            default_target_years=normalized_home_purchase_goal["target_years"],
        ),
        "home_purchase_goal": normalized_home_purchase_goal,
    }

    for goal in normalized["special_goals"]:
        if str(goal.get("name", "")).strip() == "二쇳깮?먭툑":
            goal["target_years"] = normalized_home_purchase_goal["target_years"]

    if birth_year and (birth_year < 1900 or birth_year > today.year):
        errors.append("출생년도 범위가 올바르지 않습니다.")
    if birth_month and not 1 <= birth_month <= 12:
        errors.append("출생월은 1~12 사이여야 합니다.")
    if birth_day and not 1 <= birth_day <= 31:
        errors.append("출생일은 1~31 사이여야 합니다.")
    if age and (age < 20 or age > 100):
        warnings.append("나이가 보고서 비교 범위(20~64세)를 벗어나 fallback 기준이 적용될 수 있습니다.")

    for key in (
        "household_income",
        "monthly_expense",
        "monthly_debt_payment",
        "monthly_saving_investment",
        "monthly_emergency_fund",
        "average_consumption",
        "liquid_assets",
        "non_liquid_assets",
    ):
        if normalized[key] < 0:
            errors.append(f"{key} 값은 음수일 수 없습니다.")

    expense_categories = raw.get("expense_categories", {}) or {}
    normalized_categories = {}
    category_sum = 0.0
    for key, label in EXPENSE_CATEGORY_LABELS.items():
        value = _to_number(expense_categories.get(key, 0), label, errors, allow_blank=True)
        normalized_categories[key] = value
        category_sum += value
    normalized["expense_categories"] = normalized_categories

    if normalized["monthly_expense"] > 0:
        gap = abs(category_sum - normalized["monthly_expense"])
        if gap > max(20, normalized["monthly_expense"] * 0.1):
            warnings.append(
                f"소비 세부합계({category_sum:.0f})와 월 소비/지출({normalized['monthly_expense']:.0f}) 차이가 있습니다."
            )

    saving_products = raw.get("saving_products", {}) or {}
    insurance_products = raw.get("insurance_products", {}) or {}

    normalized_products = {}
    for key in PRODUCT_INPUT_GROUPS["general"] + PRODUCT_INPUT_GROUPS["tax_benefit"]:
        normalized_products[key] = _to_number(
            saving_products.get(key, 0),
            PRODUCT_LABELS[key],
            errors,
            allow_blank=True,
        )

    legacy_insurance = _to_number(
        saving_products.get("insurance", 0),
        PRODUCT_LABELS["insurance"],
        errors,
        allow_blank=True,
    )
    normalized_insurance = {}
    insurance_sum = 0.0
    for key, label in INSURANCE_PRODUCT_LABELS.items():
        value = _to_number(insurance_products.get(key, 0), label, errors, allow_blank=True)
        normalized_insurance[key] = value
        insurance_sum += value

    if insurance_sum > 0:
        normalized_products["insurance"] = 0.0
    else:
        normalized_products["insurance"] = legacy_insurance

    for key, value in normalized_insurance.items():
        normalized_products[key] = value

    normalized["insurance_products"] = normalized_insurance
    normalized["saving_products"] = normalized_products

    product_sum = sum(normalized_products.values())
    if normalized["monthly_saving_investment"] > 0:
        gap = abs(product_sum - normalized["monthly_saving_investment"])
        if gap > max(10, normalized["monthly_saving_investment"] * 0.1):
            warnings.append(
                f"상품별 합계({product_sum:.0f})와 월 저축/투자({normalized['monthly_saving_investment']:.0f}) 차이가 있습니다."
            )

    pension = raw.get("pension", {}) or {}
    normalized["pension"] = {
        "current_age": int(_to_number(pension.get("current_age", normalized["age"]), "연금 현재 나이", errors, allow_blank=True)),
        "retirement_age": int(_to_number(pension.get("retirement_age", 60), "연금 수령 나이", errors, allow_blank=True)),
        "expected_monthly_pension": _to_number(pension.get("expected_monthly_pension", 0), "기대 월연금", errors, allow_blank=True),
        "current_balance": _to_number(pension.get("current_balance", 0), "현재 연금 적립액", errors, allow_blank=True),
    }

    if normalized["pension"]["retirement_age"] <= normalized["pension"]["current_age"]:
        warnings.append("연금 수령 나이가 현재 나이보다 커야 합니다. 계산 시 최소 1년 뒤로 보정합니다.")

    total_outflow = (
        normalized["monthly_expense"]
        + normalized["monthly_debt_payment"]
        + normalized["monthly_saving_investment"]
        + normalized["monthly_emergency_fund"]
    )
    if normalized["household_income"] > 0 and total_outflow > normalized["household_income"]:
        warnings.append("현재 입력 기준으로 월 현금흐름이 적자입니다.")

    return normalized, errors, warnings
