from typing import Dict, List

from config import BENCHMARK_PRODUCT_LABELS, INSURANCE_PRODUCT_LABELS


GOOD_TONE = "good"
BAD_TONE = "bad"
NEUTRAL_TONE = "neutral"


def _format_number(value: float) -> str:
    text = f"{float(value):,.1f}"
    return text.rstrip("0").rstrip(".")


def _format_money(value: float) -> str:
    return f"{_format_number(value)}만원"


def _format_signed_money(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{_format_money(value)}"


def _format_ratio(value: float) -> str:
    return f"{float(value) * 100:.1f}%"


def _format_signed_ratio(value: float) -> str:
    return f"{float(value) * 100:+.1f}%"


def _format_benefit(min_value: float, max_value: float) -> str:
    if max_value <= 0:
        return "0만원"
    if abs(max_value - min_value) < 1e-9:
        return _format_money(max_value)
    return f"{_format_money(min_value)}~{_format_money(max_value)}"


def _format_months(value: float) -> str:
    return f"{float(value):,.1f}개월"


def _judgement_label(tone: str) -> str:
    return {
        GOOD_TONE: "양호",
        BAD_TONE: "불량",
        NEUTRAL_TONE: "점검",
    }.get(tone, "점검")


def _table(section_id: str, title: str, description: str, columns: List[dict], rows: List[dict]) -> dict:
    return {
        "id": section_id,
        "title": title,
        "description": description,
        "columns": columns,
        "rows": rows,
    }


def _higher_is_better_tone(actual: float, benchmark: float, tolerance: float = 0.10) -> str:
    if benchmark <= 0:
        return GOOD_TONE if actual > 0 else NEUTRAL_TONE
    if actual < benchmark * (1.0 - tolerance):
        return BAD_TONE
    return GOOD_TONE


def _lower_is_better_tone(actual: float, benchmark: float, tolerance: float = 0.10) -> str:
    if benchmark <= 0:
        return GOOD_TONE if actual <= 0 else BAD_TONE
    if actual > benchmark * (1.0 + tolerance):
        return BAD_TONE
    return GOOD_TONE


def _alignment_tone(gap_ratio: float, good_threshold: float = 0.05, bad_threshold: float = 0.10) -> str:
    absolute_gap = abs(gap_ratio)
    if absolute_gap <= good_threshold:
        return GOOD_TONE
    if absolute_gap >= bad_threshold:
        return BAD_TONE
    return NEUTRAL_TONE


def _build_metric_table(analysis) -> dict:
    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual", "title": "현재값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benchmark", "title": "기준값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap", "title": "차이", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap_rate", "title": "차이율", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]
    rows = []
    lower_is_better = {"expense", "debt_payment"}
    ordered_keys = [
        "household_income",
        "expense",
        "debt_payment",
        "saving_investment",
        "emergency_fund",
        "total_assets",
        "financial_assets_proxy",
        "real_estate_assets_proxy",
    ]

    for key in ordered_keys:
        comparison = analysis.metric_comparisons[key]
        tone = (
            _lower_is_better_tone(comparison.actual_value, comparison.benchmark_value)
            if key in lower_is_better
            else _higher_is_better_tone(comparison.actual_value, comparison.benchmark_value)
        )
        rows.append(
            {
                "key": key,
                "tone": tone,
                "values": {
                    "item": comparison.label,
                    "actual": _format_money(comparison.actual_value),
                    "benchmark": _format_money(comparison.benchmark_value),
                    "gap": _format_signed_money(comparison.gap),
                    "gap_rate": _format_signed_ratio(comparison.gap_rate),
                    "judgement": _judgement_label(tone),
                },
            }
        )

    return _table(
        "metrics",
        "핵심 지표 비교",
        "보고서 기준값과 현재 가구 상태를 직접 비교합니다.",
        columns,
        rows,
    )


def _build_emergency_table(analysis) -> dict:
    emergency = analysis.emergency_rule_result
    current_balance = float(emergency.get("current_balance", 0.0))
    target_balance = float(emergency.get("target_balance", 0.0))
    months_cover = float(emergency.get("months_cover", 0.0))
    gap_rate = 0.0 if target_balance <= 0 else (current_balance - target_balance) / target_balance
    months_gap_rate = 0.0 if 6.0 <= 0 else (months_cover - 6.0) / 6.0

    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual", "title": "현재값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benchmark", "title": "기준값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap", "title": "차이", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap_rate", "title": "차이율", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]
    rows = [
        {
            "key": "emergency_balance",
            "tone": _higher_is_better_tone(current_balance, target_balance, tolerance=0.0),
            "values": {
                "item": "예비자금 잔액",
                "actual": _format_money(current_balance),
                "benchmark": _format_money(target_balance),
                "gap": _format_signed_money(current_balance - target_balance),
                "gap_rate": _format_signed_ratio(gap_rate),
                "judgement": _judgement_label(
                    _higher_is_better_tone(current_balance, target_balance, tolerance=0.0)
                ),
            },
        },
        {
            "key": "months_cover",
            "tone": GOOD_TONE if months_cover >= 6.0 else BAD_TONE if months_cover < 3.0 else NEUTRAL_TONE,
            "values": {
                "item": "생활비 방어 개월 수",
                "actual": _format_months(months_cover),
                "benchmark": _format_months(6.0),
                "gap": f"{months_cover - 6.0:+.1f}개월",
                "gap_rate": _format_signed_ratio(months_gap_rate),
                "judgement": _judgement_label(
                    GOOD_TONE if months_cover >= 6.0 else BAD_TONE if months_cover < 3.0 else NEUTRAL_TONE
                ),
            },
        },
    ]

    return _table(
        "emergency",
        "예비자금 비교",
        "규칙 기준 6개월 생활비 방어력을 비교합니다.",
        columns,
        rows,
    )


def _build_pension_table(profile, analysis) -> dict:
    pension = analysis.pension_result
    current_monthly_contribution = float(profile.saving_products.get("pension_savings", 0.0)) + float(
        profile.saving_products.get("irp", 0.0)
    )
    required_monthly_contribution = float(pension.get("required_monthly_contribution", 0.0))
    future_value = float(pension.get("future_value_of_current_balance", 0.0))
    target_capital = float(pension.get("target_capital_at_retirement", 0.0))
    contribution_gap_rate = (
        0.0
        if required_monthly_contribution <= 0
        else (current_monthly_contribution - required_monthly_contribution) / required_monthly_contribution
    )
    capital_gap_rate = 0.0 if target_capital <= 0 else (future_value - target_capital) / target_capital

    rows = [
        {
            "key": "monthly_contribution",
            "tone": _higher_is_better_tone(current_monthly_contribution, required_monthly_contribution, tolerance=0.0),
            "values": {
                "item": "연금계좌 월 납입액",
                "actual": _format_money(current_monthly_contribution),
                "benchmark": _format_money(required_monthly_contribution),
                "gap": _format_signed_money(current_monthly_contribution - required_monthly_contribution),
                "gap_rate": _format_signed_ratio(contribution_gap_rate),
                "judgement": _judgement_label(
                    _higher_is_better_tone(current_monthly_contribution, required_monthly_contribution, tolerance=0.0)
                ),
            },
        },
        {
            "key": "target_capital",
            "tone": _higher_is_better_tone(future_value, target_capital, tolerance=0.0),
            "values": {
                "item": "은퇴 시점 적립금",
                "actual": _format_money(future_value),
                "benchmark": _format_money(target_capital),
                "gap": _format_signed_money(future_value - target_capital),
                "gap_rate": _format_signed_ratio(capital_gap_rate),
                "judgement": _judgement_label(
                    _higher_is_better_tone(future_value, target_capital, tolerance=0.0)
                ),
            },
        },
    ]

    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual", "title": "현재값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benchmark", "title": "기준값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap", "title": "차이", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap_rate", "title": "차이율", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]

    return _table(
        "pension",
        "연금 준비 비교",
        "물가 반영 연금 목표와 현재 준비 수준을 비교합니다.",
        columns,
        rows,
    )


def _build_category_table(analysis) -> dict:
    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual", "title": "현재값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benchmark", "title": "기준값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap", "title": "차이", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap_rate", "title": "차이율", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]
    rows = []
    for key, comparison in analysis.category_comparisons.items():
        tone = _lower_is_better_tone(comparison.actual_value, comparison.benchmark_value, tolerance=0.15)
        rows.append(
            {
                "key": key,
                "tone": tone,
                "values": {
                    "item": comparison.label,
                    "actual": _format_money(comparison.actual_value),
                    "benchmark": _format_money(comparison.benchmark_value),
                    "gap": _format_signed_money(comparison.gap),
                    "gap_rate": _format_signed_ratio(comparison.gap_rate),
                    "judgement": _judgement_label(tone),
                },
            }
        )

    return _table(
        "categories",
        "소비 세부 비교",
        "소비 세부 항목을 기준값과 비교합니다.",
        columns,
        rows,
    )


def _build_product_table(analysis) -> dict:
    columns = [
        {"id": "item", "title": "상품", "anchor": "w", "width": 16, "weight": 2},
        {"id": "actual_amount", "title": "현재금액", "anchor": "e", "width": 12, "weight": 1},
        {"id": "actual_ratio", "title": "현재비중", "anchor": "e", "width": 10, "weight": 1},
        {"id": "benchmark_ratio", "title": "기준비중", "anchor": "e", "width": 10, "weight": 1},
        {"id": "gap_ratio", "title": "차이비중", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]
    rows = []
    product_analysis = analysis.saving_product_analysis

    for key in BENCHMARK_PRODUCT_LABELS:
        comparison = product_analysis.product_comparisons[key]
        tone = _alignment_tone(comparison.gap_ratio)
        rows.append(
            {
                "key": key,
                "tone": tone,
                "values": {
                    "item": comparison.label,
                    "actual_amount": _format_money(comparison.actual_amount),
                    "actual_ratio": _format_ratio(comparison.actual_ratio),
                    "benchmark_ratio": _format_ratio(comparison.benchmark_ratio),
                    "gap_ratio": _format_signed_ratio(comparison.gap_ratio),
                    "judgement": _judgement_label(tone),
                },
            }
        )

    return _table(
        "products",
        "상품 구성 비교",
        "보고서 금융상품 비중 기준과 현재 월 납입 구성을 비교합니다.",
        columns,
        rows,
    )


def _build_tax_benefit_table(analysis) -> dict:
    product_analysis = analysis.saving_product_analysis
    columns = [
        {"id": "item", "title": "상품", "anchor": "w", "width": 18, "weight": 2},
        {"id": "monthly", "title": "월납입", "anchor": "e", "width": 10, "weight": 1},
        {"id": "annual", "title": "연납입", "anchor": "e", "width": 10, "weight": 1},
        {"id": "benchmark", "title": "세제기준", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benefit", "title": "예상혜택", "anchor": "e", "width": 14, "weight": 1},
        {"id": "utilization", "title": "활용률", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]

    rows = []
    pension_products = [
        item
        for key, item in product_analysis.tax_benefit_products.items()
        if item.detail.get("combined_group") == "pension_account"
    ]
    if pension_products:
        combined_cap = max(float(item.detail.get("combined_cap") or 0.0) for item in pension_products)
        annual_total = sum(float(item.annual_amount) for item in pension_products)
        benefit_min = sum(float(item.estimated_benefit_min) for item in pension_products)
        benefit_max = sum(float(item.estimated_benefit_max) for item in pension_products)
        utilization = 0.0 if combined_cap <= 0 else min(annual_total, combined_cap) / combined_cap
        tone = GOOD_TONE if utilization >= 0.9 else BAD_TONE if utilization < 0.5 else NEUTRAL_TONE
        rows.append(
            {
                "key": "pension_account_total",
                "tone": tone,
                "values": {
                    "item": "연금계좌 합산",
                    "monthly": _format_money(annual_total / 12.0),
                    "annual": _format_money(annual_total),
                    "benchmark": _format_money(combined_cap),
                    "benefit": _format_benefit(benefit_min, benefit_max),
                    "utilization": _format_ratio(utilization),
                    "judgement": _judgement_label(tone),
                },
            }
        )

    for key, item in product_analysis.tax_benefit_products.items():
        annual_cap = float(item.detail.get("annual_cap") or 0.0)
        utilization = 0.0 if annual_cap <= 0 else min(item.annual_amount, annual_cap) / annual_cap
        if item.detail.get("combined_group"):
            tone = NEUTRAL_TONE
        else:
            tone = GOOD_TONE if utilization >= 0.9 else BAD_TONE if utilization < 0.5 else NEUTRAL_TONE
        benefit_text = (
            _format_benefit(item.estimated_benefit_min, item.estimated_benefit_max)
            if item.benefit_type == "tax_credit"
            else _format_money(item.deduction_base_amount)
        )
        rows.append(
            {
                "key": key,
                "tone": tone,
                "values": {
                    "item": item.label,
                    "monthly": _format_money(item.monthly_amount),
                    "annual": _format_money(item.annual_amount),
                    "benchmark": _format_money(annual_cap),
                    "benefit": benefit_text,
                    "utilization": _format_ratio(utilization),
                    "judgement": _judgement_label(tone),
                },
            }
        )

    return _table(
        "tax_benefits",
        "세제혜택 활용 비교",
        "세제혜택 상품의 납입액을 세법상 한도 기준과 비교합니다.",
        columns,
        rows,
    )


def _build_home_purchase_table(profile, analysis) -> dict:
    home = analysis.home_purchase_result
    down_payment_target = float(home.get("down_payment_target", 0.0))
    required_monthly_saving = float(home.get("required_monthly_saving", 0.0))
    monthly_repayment = float(home.get("monthly_repayment", 0.0))
    dti_limit_payment = float(home.get("dti_limit_payment", 0.0))

    liquidity_gap_rate = 0.0 if down_payment_target <= 0 else (profile.liquid_assets - down_payment_target) / down_payment_target
    saving_gap_rate = (
        0.0
        if required_monthly_saving <= 0
        else (profile.monthly_saving_investment - required_monthly_saving) / required_monthly_saving
    )
    repayment_gap_rate = (
        0.0 if dti_limit_payment <= 0 else (monthly_repayment - dti_limit_payment) / dti_limit_payment
    )

    rows = [
        {
            "key": "down_payment",
            "tone": _higher_is_better_tone(profile.liquid_assets, down_payment_target, tolerance=0.0),
            "values": {
                "item": "필요 자기자금",
                "actual": _format_money(profile.liquid_assets),
                "benchmark": _format_money(down_payment_target),
                "gap": _format_signed_money(profile.liquid_assets - down_payment_target),
                "gap_rate": _format_signed_ratio(liquidity_gap_rate),
                "judgement": _judgement_label(
                    _higher_is_better_tone(profile.liquid_assets, down_payment_target, tolerance=0.0)
                ),
            },
        },
        {
            "key": "monthly_saving",
            "tone": _higher_is_better_tone(profile.monthly_saving_investment, required_monthly_saving, tolerance=0.0),
            "values": {
                "item": "목표 월저축액",
                "actual": _format_money(profile.monthly_saving_investment),
                "benchmark": _format_money(required_monthly_saving),
                "gap": _format_signed_money(profile.monthly_saving_investment - required_monthly_saving),
                "gap_rate": _format_signed_ratio(saving_gap_rate),
                "judgement": _judgement_label(
                    _higher_is_better_tone(profile.monthly_saving_investment, required_monthly_saving, tolerance=0.0)
                ),
            },
        },
        {
            "key": "monthly_repayment",
            "tone": _lower_is_better_tone(monthly_repayment, dti_limit_payment, tolerance=0.0),
            "values": {
                "item": "DTI 대비 월상환액",
                "actual": _format_money(monthly_repayment),
                "benchmark": _format_money(dti_limit_payment),
                "gap": _format_signed_money(monthly_repayment - dti_limit_payment),
                "gap_rate": _format_signed_ratio(repayment_gap_rate),
                "judgement": _judgement_label(
                    _lower_is_better_tone(monthly_repayment, dti_limit_payment, tolerance=0.0)
                ),
            },
        },
    ]

    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual", "title": "현재값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benchmark", "title": "기준값", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap", "title": "차이", "anchor": "e", "width": 12, "weight": 1},
        {"id": "gap_rate", "title": "차이율", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]

    return _table(
        "home_purchase",
        "내 집 마련 비교",
        "목표 주택가격, LTV, DTI 기준으로 현재 준비 수준을 비교합니다.",
        columns,
        rows,
    )


def _build_insurance_table(profile) -> dict:
    total_insurance = max(profile.total_insurance_premium, 0.0)
    columns = [
        {"id": "item", "title": "상품", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual", "title": "월납입", "anchor": "e", "width": 12, "weight": 1},
        {"id": "share", "title": "보험내 비중", "anchor": "e", "width": 12, "weight": 1},
        {"id": "judgement", "title": "구분", "anchor": "center", "width": 8, "weight": 1},
    ]
    rows = []
    for key, label in INSURANCE_PRODUCT_LABELS.items():
        amount = float(profile.insurance_products.get(key, 0.0))
        share = 0.0 if total_insurance <= 0 else amount / total_insurance
        rows.append(
            {
                "key": key,
                "tone": NEUTRAL_TONE,
                "values": {
                    "item": label,
                    "actual": _format_money(amount),
                    "share": _format_ratio(share),
                    "judgement": "참고",
                },
            }
        )

    return _table(
        "insurance_detail",
        "보험 세부 구성",
        "보험 세부 구성은 현재 입력 현황 참고용입니다.",
        columns,
        rows,
    )


def _income_flow_tone(flow_key: str, comparison) -> str:
    if flow_key in {"expense", "debt_payment"}:
        return _lower_is_better_tone(comparison.actual_ratio, comparison.benchmark_ratio, tolerance=0.10)
    return _higher_is_better_tone(comparison.actual_ratio, comparison.benchmark_ratio, tolerance=0.10)


def _build_income_allocation_table(analysis) -> dict:
    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "actual_amount", "title": "현재금액", "anchor": "e", "width": 12, "weight": 1},
        {"id": "benchmark_amount", "title": "기준금액", "anchor": "e", "width": 12, "weight": 1},
        {"id": "actual_ratio", "title": "현재비중", "anchor": "e", "width": 10, "weight": 1},
        {"id": "benchmark_ratio", "title": "기준비중", "anchor": "e", "width": 10, "weight": 1},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]
    rows = []
    for flow_key in ("expense", "debt_payment", "saving_investment", "emergency_fund"):
        comparison = analysis.income_allocation_comparisons.get(flow_key)
        if comparison is None:
            continue
        tone = _income_flow_tone(flow_key, comparison)
        rows.append(
            {
                "key": flow_key,
                "tone": tone,
                "values": {
                    "item": comparison.label,
                    "actual_amount": _format_money(comparison.actual_amount),
                    "benchmark_amount": _format_money(comparison.benchmark_amount),
                    "actual_ratio": _format_ratio(comparison.actual_ratio),
                    "benchmark_ratio": _format_ratio(comparison.benchmark_ratio),
                    "judgement": _judgement_label(tone),
                },
            }
        )

    return _table(
        "income_allocation",
        "소득운용 비교",
        "보고서 소득운용 현황의 금액과 총소득 대비 비중을 현재 가구와 비교합니다.",
        columns,
        rows,
    )


def _build_dominant_expense_table(analysis) -> dict:
    dominant = analysis.dominant_expense_analysis
    if dominant is None:
        return _table("dominant_expense", "대표 정기지출", "", [], [])

    tone = _alignment_tone(dominant.actual_gap_rate, good_threshold=0.10, bad_threshold=0.20)
    columns = [
        {"id": "item", "title": "항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "benchmark", "title": "기준금액", "anchor": "e", "width": 12, "weight": 1},
        {"id": "actual", "title": "현재금액", "anchor": "e", "width": 12, "weight": 1},
        {"id": "fixed_rate", "title": "고정소비율", "anchor": "e", "width": 10, "weight": 1},
        {"id": "current_top", "title": "현재 최대항목", "anchor": "w", "width": 18, "weight": 2},
        {"id": "judgement", "title": "판정", "anchor": "center", "width": 8, "weight": 1},
    ]
    current_top_text = dominant.actual_top_label or "-"
    if dominant.actual_top_amount > 0:
        current_top_text = f"{current_top_text} ({_format_money(dominant.actual_top_amount)})"

    rows = [
        {
            "key": dominant.category_key,
            "tone": tone,
            "values": {
                "item": dominant.label,
                "benchmark": _format_money(dominant.benchmark_amount),
                "actual": _format_money(dominant.actual_amount),
                "fixed_rate": (
                    f"{float(dominant.benchmark_fixed_spend_rate):.0f}%"
                    if dominant.benchmark_fixed_spend_rate is not None
                    else "-"
                ),
                "current_top": current_top_text,
                "judgement": _judgement_label(tone),
            },
        }
    ]

    return _table(
        "dominant_expense",
        "대표 정기지출",
        "보고서 주황색 표시는 해당 소득구간에서 매월 고정/정기적으로 소비하는 금액이 가장 큰 항목입니다.",
        columns,
        rows,
    )


def build_analysis_tables(profile, analysis) -> List[dict]:
    dominant_expense_table = _build_dominant_expense_table(analysis)
    if dominant_expense_table.get("id") == "dominant_expense":
        dominant_expense_table["description"] = "해당 소득구간에서 매월 고정/정기적으로 소비하는 금액이 가장 큰 항목입니다."

    tables = [
        _build_metric_table(analysis),
        _build_income_allocation_table(analysis),
        _build_emergency_table(analysis),
        _build_pension_table(profile, analysis),
        _build_category_table(analysis),
        dominant_expense_table,
        _build_product_table(analysis),
        _build_tax_benefit_table(analysis),
        _build_home_purchase_table(profile, analysis),
        _build_insurance_table(profile),
    ]
    return [table for table in tables if table.get("rows")]
