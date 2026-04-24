from typing import List

from config import BENCHMARK_PRODUCT_LABELS, INSURANCE_PRODUCT_LABELS
from output_logic.diagnosis_builder import build_structured_insights


def _format_money(value: float) -> str:
    return f"{value:,.0f}만원"


def _format_precise_money(value: float) -> str:
    return f"{value:,.1f}만원"


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _format_band_range(min_income, max_income) -> str:
    if min_income is None and max_income is None:
        return "범위 정보 없음"
    if min_income is None:
        return f"{max_income:,.0f}만원 미만"
    if max_income is None:
        return f"{min_income:,.0f}만원 이상"
    return f"{min_income:,.0f}만원 이상 {max_income:,.0f}만원 미만"


def _product_status_label(status: str) -> str:
    status_map = {
        "overweight": "비중 높음",
        "underweight": "비중 낮음",
        "aligned": "유사",
        "tilted": "다소 차이",
    }
    return status_map.get(status, status)


def _format_benefit_range(min_value: float, max_value: float) -> str:
    if max_value <= 0:
        return "0만원"
    if abs(min_value - max_value) < 1e-9:
        return _format_precise_money(max_value)
    return f"{_format_precise_money(min_value)}~{_format_precise_money(max_value)}"


def _format_relative_status(status: str) -> str:
    status_map = {
        "높음": "기준보다 높음",
        "낮음": "기준보다 낮음",
        "유사": "기준과 유사",
    }
    return status_map.get(status, status)


def _relative_status_from_gap_rate(gap_rate: float) -> str:
    if gap_rate <= -0.10:
        return "낮음"
    if gap_rate >= 0.10:
        return "높음"
    return "유사"


def build_summary_text(profile, analysis) -> str:
    lines: List[str] = []
    selection = analysis.benchmark_selection
    insights = build_structured_insights(profile, analysis)

    lines.append("[비교 기준]")
    lines.append(
        f"- 비교 그룹: Group {selection.group_id} / {selection.group_title} / 소득구간 {selection.band_key}"
    )
    lines.append(
        f"- 소득 범위: {_format_band_range(selection.band_min_income, selection.band_max_income)} / 기준 평균소득 {_format_money(selection.band_income)} / 선택 방식 {selection.selection_method}"
    )
    if selection.fallback_note:
        lines.append(f"- fallback 적용: {selection.fallback_note}")

    lines.append("")
    lines.append("[기본 정보]")
    lines.append(f"- 이름: {profile.name or '-'} / 성별: {profile.gender or '-'} / 나이: {profile.age}")
    if profile.birth_year:
        birth_text = f"{profile.birth_year}"
        if profile.birth_month:
            birth_text += f"-{profile.birth_month:02d}"
        if profile.birth_day:
            birth_text += f"-{profile.birth_day:02d}"
        lines.append(f"- 출생일: {birth_text}")

    lines.append("")
    lines.append("[핵심 진단]")
    for item in insights["core_diagnoses"]:
        lines.append(f"- {item['title']}: {item['message']}")

    lines.append("")
    lines.append("[주요 비교]")
    for key in ("household_income", "expense", "debt_payment", "saving_investment", "total_assets"):
        comparison = analysis.metric_comparisons[key]
        lines.append(
            f"- {comparison.label}: 기준 {_format_money(comparison.benchmark_value)}, 현재 {_format_money(comparison.actual_value)}, 판정 {comparison.status}"
        )

    if analysis.income_allocation_comparisons:
        lines.append("")
        lines.append("[소득운용 분석]")
        lines.append("- 기준 비중은 총소득 중 해당 지출금액이 차지하는 비중입니다.")
        for flow_key in ("expense", "debt_payment", "saving_investment", "emergency_fund"):
            comparison = analysis.income_allocation_comparisons.get(flow_key)
            if comparison is None:
                continue
            lines.append(
                f"- {comparison.label}: 기준 {_format_pct(comparison.benchmark_ratio)} ({_format_money(comparison.benchmark_amount)}), "
                f"현재 {_format_pct(comparison.actual_ratio)} ({_format_money(comparison.actual_amount)}), "
                f"판정 {_format_relative_status(comparison.status)}"
            )

    lines.append("")
    lines.append("[현금흐름]")
    lines.append(f"- 월수입: {_format_money(profile.household_income)}")
    lines.append(f"- 월지출합계: {_format_money(profile.total_monthly_outflow)}")
    lines.append(f"- 월잉여/부족: {_format_money(profile.monthly_surplus)}")

    lines.append("")
    lines.append("[계산 가정]")
    assumptions = profile.economic_assumptions
    lines.append(f"- 물가상승률: {_format_pct(assumptions.inflation_rate)}")
    lines.append(f"- 투자 수익률: {_format_pct(assumptions.investment_return_rate)}")
    lines.append(f"- 적금 수익률: {_format_pct(assumptions.installment_return_rate)}")
    lines.append(f"- 연금 적립 수익률: {_format_pct(assumptions.pension_accumulation_return_rate)}")
    lines.append(f"- 연금 수령 수익률: {_format_pct(assumptions.pension_payout_return_rate)}")

    lines.append("")
    lines.append("[예비자금]")
    emergency = analysis.emergency_rule_result
    lines.append(
        f"- 목표 예비자금(6개월): {_format_money(emergency['target_balance'])}, 현재 현금성 자산 {_format_money(emergency['current_balance'])}"
    )
    lines.append(f"- 방어력: 월 소비 기준 {emergency['months_cover']:.1f}개월")

    lines.append("")
    lines.append("[연금 계산]")
    pension = analysis.pension_result
    lines.append(
        f"- 수령시점 목표 월연금(물가 반영): {_format_money(pension['inflation_adjusted_monthly_pension_at_retirement'])}"
    )
    lines.append(f"- 목표 적립금: {_format_money(pension['target_capital_at_retirement'])}")
    lines.append(f"- 현재 적립금 미래가치: {_format_money(pension['future_value_of_current_balance'])}")
    lines.append(f"- 필요 월 납입액: {_format_money(pension['required_monthly_contribution'])}")

    lines.append("")
    lines.append("[저축/투자 상품 구성]")
    product_analysis = analysis.saving_product_analysis
    dominant_label = BENCHMARK_PRODUCT_LABELS.get(
        product_analysis.dominant_product_key,
        product_analysis.dominant_product_key,
    )
    if dominant_label:
        lines.append(
            f"- 주력 상품: {dominant_label} / 비중 {_format_pct(product_analysis.dominant_product_ratio)} / 편중 위험 {product_analysis.concentration_risk}"
        )
    for item in product_analysis.product_comparisons.values():
        lines.append(
            f"- {item.label}: 현재 {_format_money(item.actual_amount)} ({_format_pct(item.actual_ratio)}), 기준 {_format_pct(item.benchmark_ratio)}, 상태 {_product_status_label(item.status)}"
        )
        lines.append(f"  {item.narrative}")

    lines.append("")
    lines.append("[세제혜택 상품]")
    if product_analysis.tax_benefit_products:
        lines.append(
            f"- 예상 세액공제 합계: {_format_benefit_range(product_analysis.total_estimated_tax_benefit_min, product_analysis.total_estimated_tax_benefit_max)}"
        )
        if product_analysis.total_deduction_base_amount > 0:
            lines.append(f"- 소득공제 대상액 합계: {_format_precise_money(product_analysis.total_deduction_base_amount)}")
        for item in product_analysis.tax_benefit_products.values():
            if item.benefit_type == "tax_credit":
                lines.append(
                    f"- {item.label}: 월 {_format_money(item.monthly_amount)} / 연 {_format_money(item.annual_amount)} / 세액공제 대상 {_format_money(item.benefit_base_amount)} / 예상 세액공제 {_format_benefit_range(item.estimated_benefit_min, item.estimated_benefit_max)}"
                )
            else:
                lines.append(
                    f"- {item.label}: 월 {_format_money(item.monthly_amount)} / 연 {_format_money(item.annual_amount)} / 소득공제 대상액 {_format_precise_money(item.deduction_base_amount)}"
                )
            lines.append(f"  {item.narrative}")
    else:
        lines.append("- 세제혜택 상품 납입이 입력되지 않았습니다.")

    lines.append("")
    lines.append("[내 집 마련 계획]")
    home = analysis.home_purchase_result
    lines.append(
        f"- 목표 주택가격: {_format_money(home['house_price'])} / LTV {_format_pct(home['ltv'])} / DTI {_format_pct(home['dti'])}"
    )
    lines.append(
        f"- 목표 기간: {home['target_years']}년 / 필요 자기자금 {_format_money(home['down_payment_target'])} / 필요 월저축 {_format_precise_money(home['required_monthly_saving'])}"
    )
    lines.append(
        f"- 대출금액: {_format_money(home['loan_amount'])} / 대출 기간 {home['loan_term_years']}년 / 금리 {_format_pct(home['loan_interest_rate'])}"
    )
    lines.append(
        f"- 예상 월상환액: {_format_precise_money(home['monthly_repayment'])} / DTI 허용 월상환액 {_format_precise_money(home['dti_limit_payment'])}"
    )
    if home["within_dti_limit"] is not None:
        status_text = "DTI 범위 이내" if home["within_dti_limit"] else "DTI 범위 초과 가능"
        lines.append(
            f"- 상환 부담 체크: {status_text} / 소득 대비 상환비중 {_format_pct(home['repayment_to_income_ratio'])}"
        )

    lines.append("")
    lines.append("[보험 구성]")
    insurance_total = 0.0
    for key, label in INSURANCE_PRODUCT_LABELS.items():
        amount = profile.insurance_products.get(key, 0.0)
        insurance_total += amount
        lines.append(f"- {label}: {_format_money(amount)}")
    lines.append(f"- 월 보험료 합계: {_format_money(insurance_total)}")

    lines.append("")
    lines.append("[소비 세부항목 비교]")
    lines.append("※ 주거비는 월세성 주거비 기준이며, 전세대출/주택담보대출 상환은 부채상환 항목에서 별도로 비교합니다.")
    lines.append("※ 고정소비율: 각 소비 항목별 매월 고정/정기적으로 소비하고 있는 응답자 비율.")
    interesting = sorted(
        analysis.category_comparisons.values(),
        key=lambda item: abs(item.gap_rate),
        reverse=True,
    )[:5]
    for item in interesting:
        rate_text = f", 고정소비율 {item.fixed_spend_rate}%" if item.fixed_spend_rate is not None else ""
        lines.append(
            f"- {item.label}: 기준 {_format_money(item.benchmark_value)}, 현재 {_format_money(item.actual_value)}, 판정 {item.status}{rate_text}"
        )

    dominant_expense = analysis.dominant_expense_analysis
    if dominant_expense is not None:
        lines.append("")
        lines.append("[대표 정기지출]")
        lines.append("※ 해당 소득구간에서 매월 고정/정기적으로 소비하는 금액이 가장 큰 항목입니다.")
        rate_text = (
            f" / 고정소비율 {dominant_expense.benchmark_fixed_spend_rate}%"
            if dominant_expense.benchmark_fixed_spend_rate is not None
            else ""
        )
        lines.append(
            f"- 비교군 대표 항목: {dominant_expense.label} / 기준 {_format_money(dominant_expense.benchmark_amount)}{rate_text}"
        )
        dominant_status = _relative_status_from_gap_rate(dominant_expense.actual_gap_rate)
        lines.append(
            f"- 현재 해당 항목 지출: {_format_money(dominant_expense.actual_amount)} / 기준 대비 {_format_relative_status(dominant_status)}"
        )
        if dominant_expense.actual_top_label:
            if dominant_expense.matches_actual_top:
                lines.append(f"- 현재 입력에서도 {dominant_expense.actual_top_label}가 가장 큰 소비항목입니다.")
            else:
                lines.append(
                    f"- 현재 입력에서 가장 큰 소비항목은 {dominant_expense.actual_top_label} ({_format_money(dominant_expense.actual_top_amount)})입니다."
                )

    if profile.special_goals:
        lines.append("")
        lines.append("[특별 목표 자금]")
        lines.append(f"- 목표 총액: {_format_money(profile.total_special_goal_amount)}")
        for goal in profile.special_goals:
            lines.append(f"- {goal.name}: {_format_money(goal.target_amount)}")

    if insights["caution_items"]:
        lines.append("")
        lines.append("[주의 항목]")
        for item in insights["caution_items"]:
            lines.append(f"- {item['title']}: {item['message']}")

    if insights["strengths"]:
        lines.append("")
        lines.append("[강점]")
        for item in insights["strengths"]:
            lines.append(f"- {item['title']}: {item['message']}")

    if insights["improvement_priorities"]:
        lines.append("")
        lines.append("[개선 우선순위]")
        for item in insights["improvement_priorities"]:
            lines.append(f"- {item['title']}: {item['message']}")

    return "\n".join(lines)
