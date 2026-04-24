from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class EconomicAssumptionSpec:
    key: str
    label: str
    default_rate: float
    source_name: str
    source_type: str
    usage_scope: str
    rationale: str
    used_in_current_calculation: bool
    relation_hint: str = ""


ECONOMIC_ASSUMPTION_SPECS: List[EconomicAssumptionSpec] = [
    EconomicAssumptionSpec(
        key="inflation_rate",
        label="물가상승률",
        default_rate=0.02,
        source_name="내부 기본 가정",
        source_type="internal_default",
        usage_scope="연금 물가 반영 계산",
        rationale="장기 재무설계에서 과도하지 않은 보수적 물가 가정입니다.",
        used_in_current_calculation=True,
        relation_hint="다른 명목수익률의 실질가치를 판단할 때 함께 봅니다.",
    ),
    EconomicAssumptionSpec(
        key="investment_return_rate",
        label="투자 수익률",
        default_rate=0.04,
        source_name="내부 기본 가정",
        source_type="internal_default",
        usage_scope="현재는 설명용 보조 입력",
        rationale="적금 대비 차이를 과도하게 벌리지 않는 보수적 장기 투자 예시값입니다.",
        used_in_current_calculation=False,
        relation_hint="기본 적금 수익률보다 1%p 높은 수준으로 맞췄습니다.",
    ),
    EconomicAssumptionSpec(
        key="installment_return_rate",
        label="적금 수익률",
        default_rate=0.03,
        source_name="내부 기본 가정",
        source_type="internal_default",
        usage_scope="현재는 설명용 보조 입력",
        rationale="적금·청약류를 가정한 보수적 예시값입니다.",
        used_in_current_calculation=False,
        relation_hint="투자/연금 적립 수익률의 비교 기준 역할을 합니다.",
    ),
    EconomicAssumptionSpec(
        key="pension_accumulation_return_rate",
        label="연금 적립 수익률",
        default_rate=0.04,
        source_name="내부 기본 가정",
        source_type="internal_default",
        usage_scope="연금 필요납입액 역산",
        rationale="장기 적립형 연금 운용을 일반 투자와 같은 수준의 보수적 장기 가정으로 맞췄습니다.",
        used_in_current_calculation=True,
        relation_hint="현재 기본값은 일반 투자 수익률과 동일하게 맞췄습니다.",
    ),
    EconomicAssumptionSpec(
        key="pension_payout_return_rate",
        label="연금 수령 수익률",
        default_rate=0.02,
        source_name="내부 기본 가정",
        source_type="internal_default",
        usage_scope="연금 수령기 목표자금 계산",
        rationale="수령기 자산은 적립기보다 안정적으로 운용한다는 보수 가정입니다.",
        used_in_current_calculation=True,
        relation_hint="적립기 수익률보다 낮게 두어 인출기 변동성을 보수적으로 반영합니다.",
    ),
]

ECONOMIC_ASSUMPTION_ORDER = [spec.key for spec in ECONOMIC_ASSUMPTION_SPECS]
ECONOMIC_ASSUMPTION_LABELS = {spec.key: spec.label for spec in ECONOMIC_ASSUMPTION_SPECS}
DEFAULT_ECONOMIC_ASSUMPTIONS = {
    spec.key: spec.default_rate for spec in ECONOMIC_ASSUMPTION_SPECS
}


def build_economic_assumption_entries(assumptions) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    for spec in ECONOMIC_ASSUMPTION_SPECS:
        current_value = float(getattr(assumptions, spec.key))
        entries.append(
            {
                "key": spec.key,
                "label": spec.label,
                "value": current_value,
                "default_value": spec.default_rate,
                "source_name": spec.source_name,
                "source_type": spec.source_type,
                "usage_scope": spec.usage_scope,
                "rationale": spec.rationale,
                "used_in_current_calculation": spec.used_in_current_calculation,
                "relation_hint": spec.relation_hint,
                "is_default_value": abs(current_value - spec.default_rate) < 1e-9,
            }
        )
    return entries


def build_default_percent_map(keys: Iterable[str] = None) -> Dict[str, float]:
    keys = list(keys or ECONOMIC_ASSUMPTION_ORDER)
    return {
        key: DEFAULT_ECONOMIC_ASSUMPTIONS[key] * 100.0
        for key in keys
    }
