import json
from functools import lru_cache

from calc_logic.economic_assumption_registry import build_economic_assumption_entries
from config import REPORT_BENCHMARK_FILE
from housing_context.service import CurrentHomeLoanContextService


def _format_money(value: float) -> str:
    return f"{float(value):,.0f}만원"


def _format_pct(value: float) -> str:
    return f"{float(value) * 100:.1f}%"


def _format_band_range(min_income, max_income) -> str:
    if min_income is None and max_income is None:
        return "범위 정보 없음"
    if min_income is None:
        return f"{float(max_income):,.0f}만원 미만"
    if max_income is None:
        return f"{float(min_income):,.0f}만원 이상"
    return f"{float(min_income):,.0f}만원 이상 {float(max_income):,.0f}만원 미만"


def _source_label(source: str) -> str:
    return {
        "report": "민간 보고서 기준",
        "rule": "내부 규칙 기준",
        "pension": "계산형 기준",
        "kosis_peer": "KOSIS 동일 가구 통계",
        "median_income": "기준중위소득",
    }.get(source, source or "기준 정보 없음")


def _method_label(method: str) -> str:
    return {
        "group_band_lookup": "Life Stage + 소득구간 기준 조회",
        "monthly_flow_ratio": "보고서 월 저축상품 비중 적용",
        "external_tax_rule_lookup": "외부 세법/공식 안내 기준 조회",
        "expense_multiple": "월소비 배수 규칙 적용",
        "reverse_required_contribution_with_inflation": "물가 반영 연금 역산",
        "tax_credit_cap_range": "세액공제 한도/세율 적용",
        "income_deduction_cap": "소득공제 한도 적용",
        "household_size_age_band_lookup": "가구원수 + 연령대 조회",
        "household_size_lookup": "가구원수 기준 조회",
    }.get(method, method or "적용 방식 정보 없음")


def _item(label: str, value: str, note: str = "") -> dict:
    return {
        "label": label,
        "value": value,
        "note": note,
    }


@lru_cache(maxsize=1)
def _load_report_metadata() -> dict:
    with open(REPORT_BENCHMARK_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _build_economic_assumption_section(profile) -> dict:
    items = []
    for entry in build_economic_assumption_entries(profile.economic_assumptions):
        value_state = "기본값 유지" if entry["is_default_value"] else "사용자 입력"
        calc_scope = "현재 계산 반영" if entry["used_in_current_calculation"] else "현재는 설명용"
        note_parts = [calc_scope, entry["rationale"]]
        if entry["relation_hint"]:
            note_parts.append(entry["relation_hint"])
        items.append(
            _item(
                entry["label"],
                f"{_format_pct(entry['value'])} / {value_state} / {entry['source_name']}",
                " / ".join(note_parts),
            )
        )
    items.append(
        _item(
            "경제값 해석 원칙",
            "공신력 있는 공식 통계가 아니라 내부 기본 가정입니다.",
            "현재 직접 계산에는 물가상승률, 연금 적립 수익률, 연금 수령 수익률이 반영됩니다.",
        )
    )
    return {
        "id": "economic_assumptions",
        "title": "경제가정 기준",
        "items": items,
    }


def _build_current_economic_context_section(analysis) -> list:
    economic_context = getattr(analysis, "economic_context_summary", {}) or {}
    if not economic_context:
        return []

    metrics = economic_context.get("metrics", {})
    metric_order = [
        ("cpi_yoy", "\ud3ec\uad04 \ubb3c\uac00(\uc804\ub144\ub3d9\uc6d4\ub300\ube44)"),
        ("deposit_rate_avg", "\uc608\uae08 \uae08\ub9ac"),
        ("treasury_3y_yield", "\uad6d\uace0\ucc443\ub144 \uc218\uc775\ub960"),
        ("base_rate", "\uae30\uc900\uae08\ub9ac"),
    ]
    items = [
        _item(
            "\uae30\uc900\uc77c",
            economic_context.get("as_of_date", "-"),
            "\uad00\uce21\uc9c0\ud45c\uc640 \ucd94\ucc9c \uac00\uc815\uc744 \uacc4\uc0b0\ud55c \uae30\uc900\uc77c\uc785\ub2c8\ub2e4.",
        )
    ]

    for key, label in metric_order:
        metric = metrics.get(key)
        if not metric:
            continue
        items.append(
            _item(
                label,
                _format_pct(metric.get("value", 0.0)),
                f"{metric.get('source_name', '-')} / {metric.get('as_of_date', '-')} / {metric.get('official_url', '-')}",
            )
        )

    for entry in economic_context.get("assumption_entries", []):
        recommended_value = _format_pct(entry.get("recommended_value", 0.0))
        applied_value = _format_pct(entry.get("applied_value", 0.0))
        status = "\ucd94\ucc9c\uac12 \uc801\uc6a9" if entry.get("is_recommended_applied") else "\uc0ac\uc6a9\uc790 \uc870\uc815"
        items.append(
            _item(
                f"\ucd94\ucc9c {entry.get('key', '')}",
                f"{recommended_value} / \uc2e4\uc81c {applied_value} / {status}",
                f"{entry.get('rule', '')} / {entry.get('description', '')}",
            )
        )

    for note in economic_context.get("notes", []):
        items.append(_item("\ucc38\uace0", note, ""))

    return [
        {
            "id": "economic_context",
            "title": "\ud604\uc7ac \uc0c1\ud669 \uae30\uc900",
            "items": items,
        }
    ]


def _build_home_loan_context_section(profile) -> list:
    context_summary = CurrentHomeLoanContextService().build_context_summary(profile.home_purchase_goal)
    items = [
        _item(
            "\uae30\uc900\uc77c",
            context_summary.get("as_of_date", "-"),
            "\uc8fc\ud0dd\ub300\ucd9c \uc608\uc2dc\uac12\uc744 \uacc4\uc0b0\ud55c \uae30\uc900\uc77c\uc785\ub2c8\ub2e4.",
        )
    ]
    for entry in context_summary.get("parameter_entries", []):
        recommended_value = entry.get("recommended_value", 0.0)
        applied_value = entry.get("applied_value", 0.0)
        unit = entry.get("unit", "")
        if unit == "rate" or unit == "ratio":
            recommended_text = _format_pct(recommended_value)
            applied_text = _format_pct(applied_value)
        elif unit == "years":
            recommended_text = f"{int(recommended_value)}년"
            applied_text = f"{int(applied_value)}년"
        else:
            recommended_text = str(recommended_value)
            applied_text = str(applied_value)
        items.append(
            _item(
                entry.get("label", entry.get("key", "")),
                f"권장 {recommended_text} / 적용 {applied_text}",
                f"{entry.get('source_name', '-')} / {entry.get('method', '')} / {entry.get('note', '')}",
            )
        )
    for note in context_summary.get("notes", []):
        items.append(_item("참고", note, ""))
    return [
        {
            "id": "home_loan_context",
            "title": "주택대출 예시 기준",
            "items": items,
        }
    ]


def _build_report_sections(profile, analysis) -> list:
    report_data = _load_report_metadata()
    source_info = report_data.get("source", {})
    selection = analysis.benchmark_selection
    group_page = str(source_info.get("group_data_pages", {}).get(str(selection.group_id), ""))
    saving_detail = analysis.saving_product_analysis.detail or {}
    tax_products = analysis.saving_product_analysis.tax_benefit_products
    tax_source = ""
    tax_references = []
    if tax_products:
        first_item = next(iter(tax_products.values()))
        tax_source = first_item.source
        references = first_item.detail.get("references", {})
        for key, url in references.items():
            tax_references.append(
                {
                    "label": key.replace("_", " "),
                    "url": url,
                }
            )

    metric_items = []
    ordered_metric_keys = [
        "household_income",
        "expense",
        "debt_payment",
        "saving_investment",
        "emergency_fund",
        "total_assets",
        "financial_assets_proxy",
        "real_estate_assets_proxy",
    ]
    for key in ordered_metric_keys:
        comparison = analysis.metric_comparisons.get(key)
        if comparison is None:
            continue
        metric_items.append(
            _item(
                comparison.label,
                f"기준값 {_format_money(comparison.benchmark_value)} / {_source_label(comparison.source)}",
                _method_label(comparison.method),
            )
        )

    category_count = len(analysis.category_comparisons)
    tax_reference_text = " / ".join(item["label"] for item in tax_references) if tax_references else "공식 URL 미등록"

    sections = [
        {
            "id": "core_basis",
            "title": "핵심 비교 기준",
            "items": [
                _item(
                    "기본 비교 자료",
                    f"{source_info.get('name', '-')} / {source_info.get('publisher', '-')}",
                    "가구 기준 Life Stage 보고서",
                ),
                _item(
                    "적용 그룹",
                    f"Group {selection.group_id} / {selection.group_title}",
                    f"그룹 데이터 페이지 {group_page or '-'}",
                ),
                _item(
                    "소득구간 선택",
                    f"{selection.band_key}구간 / {_format_band_range(selection.band_min_income, selection.band_max_income)}",
                    f"선택 방식 {selection.selection_method}",
                ),
            ],
        },
        {
            "id": "metric_basis",
            "title": "주요 비교 항목 근거",
            "items": metric_items,
        },
        {
            "id": "detail_basis",
            "title": "세부 분석 근거",
            "items": [
                _item(
                    "소비 세부항목 비교",
                    f"{category_count}개 항목을 보고서 동일 그룹/소득구간 기준으로 비교",
                    f"그룹 데이터 페이지 {group_page or '-'} / {_method_label('group_band_lookup')}",
                ),
                _item(
                    "상품 비중 비교",
                    f"{_source_label(analysis.saving_product_analysis.source)} / benchmark key {saving_detail.get('benchmark_key', '-')}",
                    f"{_method_label(analysis.saving_product_analysis.method)} / source page {saving_detail.get('source_page', '-')}",
                ),
                _item(
                    "세제혜택 판단",
                    tax_source or "세제혜택 상품 미사용",
                    tax_reference_text,
                ),
            ],
        },
        _build_economic_assumption_section(profile),
        {
            "id": "derived_basis",
            "title": "계산형·규칙형 기준",
            "items": [
                _item(
                    "예비자금",
                    f"월소비 {_format_money(profile.monthly_expense)} 기준 6개월 방어력",
                    _method_label(analysis.emergency_rule_result.get("method", "")),
                ),
                _item(
                    "연금 필요납입액",
                    (
                        f"현재 {profile.pension.current_age}세 / 수령 {profile.pension.retirement_age}세 / "
                        f"목표 월연금 {_format_money(profile.pension.expected_monthly_pension)}"
                    ),
                    _method_label(analysis.pension_result.get("method", "")),
                ),
                _item(
                    "연금 계산 가정",
                    (
                        f"물가 {_format_pct(profile.economic_assumptions.inflation_rate)}, "
                        f"적립수익률 {_format_pct(profile.economic_assumptions.pension_accumulation_return_rate)}, "
                        f"수령수익률 {_format_pct(profile.economic_assumptions.pension_payout_return_rate)}"
                    ),
                    "사용자 입력 또는 내부 기본가정을 반영합니다.",
                ),
            ],
        },
    ]

    if tax_references:
        sections.append(
            {
                "id": "references",
                "title": "공식 참고 링크",
                "items": [
                    _item(reference["label"], reference["url"], tax_source or "공식 세법 안내")
                    for reference in tax_references
                ],
            }
        )

    return sections


def _build_external_sections(analysis) -> list:
    external_summary = getattr(analysis, "external_benchmark_summary", {}) or {}
    if not external_summary.get("available"):
        return []

    benchmark_values = external_summary.get("benchmark_context", {}).get("values", {})
    source_status = external_summary.get("source_status", [])
    notes = external_summary.get("notes", [])
    external_analysis = external_summary.get("analysis", {})

    public_items = []
    ordered_keys = [
        ("peer_monthly_income", "KOSIS 동일 가구 평균소득"),
        ("median_income_reference", "기준중위소득"),
        ("peer_total_assets", "KOSIS 동일 가구 총자산"),
        ("peer_financial_assets", "KOSIS 동일 가구 금융자산"),
        ("peer_real_estate_assets", "KOSIS 동일 가구 부동산자산"),
        ("peer_monthly_consumption", "KOSIS 동일 가구 월소비지출"),
    ]
    for key, label in ordered_keys:
        value_payload = benchmark_values.get(key)
        if value_payload is None:
            continue
        public_items.append(
            _item(
                label,
                f"{_format_money(value_payload.get('value', 0.0))} / {value_payload.get('source_name', '-')}",
                _method_label(value_payload.get("method", "")),
            )
        )

    if external_analysis:
        income_position = external_analysis.get("income_position", {})
        asset_position = external_analysis.get("asset_position", {})
        debt_risk_level = external_analysis.get("debt_risk_level", {})
        spending_gap = external_analysis.get("spending_gap", {})
        public_items.extend(
            [
                _item(
                    "공공통계 소득 위치",
                    f"동일 가구 평균 대비 {income_position.get('vs_peer_income_ratio', 0.0) * 100:.1f}%",
                    f"수준 {income_position.get('level', '-')}",
                ),
                _item(
                    "공공통계 자산 위치",
                    f"동일 가구 평균 대비 {asset_position.get('vs_peer_total_assets_ratio', 0.0) * 100:.1f}%",
                    f"수준 {asset_position.get('level', '-')}",
                ),
                _item(
                    "공공통계 소비 위치",
                    f"동일 가구 평균 대비 {spending_gap.get('vs_peer_consumption_ratio', 0.0) * 100:.1f}%",
                    f"수준 {spending_gap.get('level', '-')}",
                ),
                _item(
                    "공공통계 부채 판단",
                    debt_risk_level.get("level", "-"),
                    "총부채 입력이 없으면 해석에 제한이 있습니다.",
                ),
            ]
        )

    source_items = []
    for row in source_status:
        source_items.append(
            _item(
                row.get("source_name", "-"),
                f"상태 {row.get('status', '-')} / version {row.get('source_version', '-')}",
                f"정규화 {row.get('normalized_count', 0)}건 / fetched_at {row.get('fetched_at', '-')}",
            )
        )

    sections = [
        {
            "id": "public_statistics",
            "title": "공공 통계 보조 근거",
            "items": public_items,
        },
        {
            "id": "public_sources",
            "title": "연동된 기준자료 상태",
            "items": source_items,
        },
    ]

    if notes:
        sections.append(
            {
                "id": "public_notes",
                "title": "통합 메모",
                "items": [_item("참고", note, "") for note in notes],
            }
        )

    return sections


def build_source_report_payload(profile, analysis) -> dict:
    report_data = _load_report_metadata()
    source_info = report_data.get("source", {})
    selection = analysis.benchmark_selection
    sections = (
        _build_report_sections(profile, analysis)
        + _build_home_loan_context_section(profile)
        + _build_current_economic_context_section(analysis)
        + _build_external_sections(analysis)
    )

    return {
        "title": "자료 근거 리포트",
        "summary": {
            "group_title": selection.group_title,
            "band_key": selection.band_key,
            "selection_method": selection.selection_method,
            "report_name": source_info.get("name", ""),
            "report_publisher": source_info.get("publisher", ""),
            "external_benchmark_available": bool(getattr(analysis, "external_benchmark_summary", {}).get("available")),
            "economic_context_available": bool(getattr(analysis, "economic_context_summary", {})),
            "economic_context_as_of_date": getattr(analysis, "economic_context_summary", {}).get("as_of_date", ""),
        },
        "sections": sections,
    }


def build_source_report_text(profile, analysis) -> str:
    payload = build_source_report_payload(profile, analysis)
    lines = [f"[{payload['title']}]"]

    for section in payload["sections"]:
        lines.append("")
        lines.append(f"[{section['title']}]")
        for item in section["items"]:
            line = f"- {item['label']}: {item['value']}"
            if item.get("note"):
                line += f" / {item['note']}"
            lines.append(line)

    return "\n".join(lines)
