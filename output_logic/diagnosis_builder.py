from typing import Dict, List

from config import BENCHMARK_PRODUCT_LABELS, CATEGORY_LABELS


def _build_item(key: str, title: str, message: str, severity: str, related_keys: List[str]) -> dict:
    return {
        "key": key,
        "title": title,
        "message": message,
        "severity": severity,
        "related_keys": related_keys,
    }


def _top_category_gap(analysis, positive: bool = True):
    candidates = [
        item
        for item in analysis.category_comparisons.values()
        if (item.gap_rate > 0 if positive else item.gap_rate < 0)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: abs(item.gap_rate))


def build_structured_insights(profile, analysis) -> Dict[str, List[dict]]:
    metrics = analysis.metric_comparisons
    emergency = analysis.emergency_rule_result
    pension = analysis.pension_result
    product_analysis = analysis.saving_product_analysis

    sections = {
        "core_diagnoses": [],
        "caution_items": [],
        "strengths": [],
        "improvement_priorities": [],
    }
    priority_candidates = []

    if profile.monthly_surplus < 0:
        sections["core_diagnoses"].append(
            _build_item(
                "cashflow_deficit",
                "월 현금흐름 적자",
                f"월 잉여자금이 {abs(profile.monthly_surplus):,.0f}만원 부족해 지출과 부채 구조를 먼저 조정할 필요가 있습니다.",
                "high",
                ["household_income", "expense", "debt_payment", "saving_investment"],
            )
        )
        priority_candidates.append(
            (
                100,
                _build_item(
                    "cashflow_deficit",
                    "현금흐름 정상화",
                    "월 적자를 먼저 해소해야 다른 재무목표를 안정적으로 집행할 수 있습니다.",
                    "high",
                    ["expense", "debt_payment"],
                ),
            )
        )
    else:
        sections["strengths"].append(
            _build_item(
                "cashflow_surplus",
                "월 잉여자금 확보",
                f"월 {profile.monthly_surplus:,.0f}만원의 잉여자금이 추가 배분 가능한 상태입니다.",
                "medium",
                ["household_income", "expense", "saving_investment"],
            )
        )

    if metrics["expense"].gap_rate > 0.10:
        sections["caution_items"].append(
            _build_item(
                "expense_high",
                "지출 수준 높음",
                f"월 지출이 비교 기준보다 {metrics['expense'].gap_rate * 100:.1f}% 높습니다.",
                "high",
                ["expense"],
            )
        )
        priority_candidates.append(
            (
                90,
                _build_item(
                    "expense_high",
                    "지출 재배치",
                    "기준보다 많이 높은 소비 항목부터 순서대로 조정하는 것이 좋습니다.",
                    "high",
                    ["expense"],
                ),
            )
        )

    if metrics["debt_payment"].gap_rate > 0.10:
        sections["caution_items"].append(
            _build_item(
                "debt_burden",
                "부채상환 부담",
                f"월 부채상환액이 비교 기준보다 {metrics['debt_payment'].gap_rate * 100:.1f}% 높습니다.",
                "high",
                ["debt_payment"],
            )
        )
        priority_candidates.append(
            (
                85,
                _build_item(
                    "debt_burden",
                    "고정 부채부담 완화",
                    "다른 목표를 늘리기 전에 금리와 상환구조 점검이 우선입니다.",
                    "high",
                    ["debt_payment"],
                ),
            )
        )

    if metrics["saving_investment"].gap_rate < -0.10:
        sections["core_diagnoses"].append(
            _build_item(
                "saving_low",
                "저축여력 부족",
                f"월 저축·투자액이 비교 기준보다 {-metrics['saving_investment'].gap_rate * 100:.1f}% 낮습니다.",
                "high",
                ["saving_investment"],
            )
        )
        priority_candidates.append(
            (
                80,
                _build_item(
                    "saving_low",
                    "저축여력 회복",
                    "고정지출 조정 후 목표 저축규모를 먼저 회복하는 것이 좋습니다.",
                    "high",
                    ["saving_investment"],
                ),
            )
        )
    else:
        sections["strengths"].append(
            _build_item(
                "saving_ok",
                "저축 수준 안정",
                "월 저축·투자 규모가 비교 기준에 근접하거나 상회합니다.",
                "medium",
                ["saving_investment"],
            )
        )

    if emergency["months_cover"] < 3:
        sections["core_diagnoses"].append(
            _build_item(
                "emergency_weak",
                "예비자금 방어력 부족",
                f"예비자금이 월 소비 기준 {emergency['months_cover']:.1f}개월분만 버틸 수 있습니다.",
                "high",
                ["emergency_fund", "financial_assets_proxy"],
            )
        )
        priority_candidates.append(
            (
                95,
                _build_item(
                    "emergency_weak",
                    "예비자금 확충",
                    "위험자산 확대 전에 최소 3~6개월 생활비 버퍼를 확보하는 것이 좋습니다.",
                    "high",
                    ["emergency_fund"],
                ),
            )
        )
    elif emergency["months_cover"] >= 6:
        sections["strengths"].append(
            _build_item(
                "emergency_good",
                "예비자금 방어력 양호",
                f"예비자금이 월 소비 기준 {emergency['months_cover']:.1f}개월분 확보되어 있습니다.",
                "medium",
                ["emergency_fund", "financial_assets_proxy"],
            )
        )

    if pension["required_monthly_contribution"] > max(profile.monthly_saving_investment, 1) * 0.6:
        sections["caution_items"].append(
            _build_item(
                "pension_gap",
                "연금 준비 부담",
                f"필요 월 연금 납입액이 {pension['required_monthly_contribution']:,.0f}만원으로 추정됩니다.",
                "medium",
                ["saving_investment"],
            )
        )
        priority_candidates.append(
            (
                70,
                _build_item(
                    "pension_gap",
                    "연금계획 재점검",
                    "은퇴 시점과 목표 월연금을 납입여력과 함께 다시 맞춰볼 필요가 있습니다.",
                    "medium",
                    ["saving_investment"],
                ),
            )
        )

    dominant_label = BENCHMARK_PRODUCT_LABELS.get(
        product_analysis.dominant_product_key,
        product_analysis.dominant_product_key,
    )
    if product_analysis.concentration_risk in {"high", "moderate"} and dominant_label:
        sections["caution_items"].append(
            _build_item(
                "product_bias",
                "상품 구성 편중",
                f"{dominant_label} 비중이 {product_analysis.dominant_product_ratio * 100:.1f}%로 높아 배분이 한쪽으로 기울어져 있습니다.",
                "medium",
                ["saving_investment"],
            )
        )
        priority_candidates.append(
            (
                60,
                _build_item(
                    "product_bias",
                    "상품 비중 재조정",
                    "유동성, 보장, 적립, 투자 기능이 균형적인지 확인이 필요합니다.",
                    "medium",
                    ["saving_investment"],
                ),
            )
        )

    if product_analysis.tax_benefit_products:
        sections["strengths"].append(
            _build_item(
                "tax_benefit_in_use",
                "세제혜택 상품 활용",
                f"현재 입력 기준 예상 세액공제는 연 {product_analysis.total_estimated_tax_benefit_min:,.1f}~{product_analysis.total_estimated_tax_benefit_max:,.1f}만원입니다.",
                "medium",
                ["saving_investment"],
            )
        )
    elif profile.monthly_saving_investment > 0:
        priority_candidates.append(
            (
                50,
                _build_item(
                    "tax_benefit_review",
                    "세제혜택 상품 검토",
                    "연금저축, IRP, 주택청약종합저축 활용 여부를 함께 점검하면 절세 여지를 찾을 수 있습니다.",
                    "low",
                    ["saving_investment"],
                ),
            )
        )

    high_category = _top_category_gap(analysis, positive=True)
    if high_category and high_category.gap_rate > 0.20:
        category_label = CATEGORY_LABELS.get(high_category.category_key, high_category.label)
        sections["caution_items"].append(
            _build_item(
                "category_gap",
                "큰 소비 항목 편차",
                f"{category_label} 지출이 비교 기준보다 {high_category.gap_rate * 100:.1f}% 높습니다.",
                "medium",
                [high_category.category_key],
            )
        )
        priority_candidates.append(
            (
                55,
                _build_item(
                    "category_gap",
                    f"{category_label} 점검",
                    "가장 차이가 큰 단일 소비 항목부터 먼저 조정하는 것이 효율적입니다.",
                    "medium",
                    [high_category.category_key],
                ),
            )
        )

    if metrics["total_assets"].gap_rate >= 0.10:
        sections["strengths"].append(
            _build_item(
                "asset_good",
                "자산 축적 양호",
                "선택된 그룹과 소득구간 대비 총자산 수준이 비교 기준보다 높습니다.",
                "medium",
                ["total_assets"],
            )
        )

    for index, warning in enumerate(analysis.warnings):
        sections["caution_items"].append(
            _build_item(
                f"warning_{index}",
                "입력 경고",
                warning,
                "low",
                [],
            )
        )

    priority_candidates.sort(key=lambda item: item[0], reverse=True)
    sections["improvement_priorities"] = [item for _, item in priority_candidates[:4]]

    if not sections["core_diagnoses"]:
        sections["core_diagnoses"].append(
            _build_item(
                "balanced",
                "기본 구조 안정",
                "핵심 지표가 비교 기준에서 크게 벗어나지 않아 세부 조정 단계로 넘어갈 수 있습니다.",
                "low",
                ["expense", "saving_investment", "total_assets"],
            )
        )

    return sections
