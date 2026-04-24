from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List

from calc_logic.analysis_service import AnalysisService
from economic_context.service import CurrentEconomicContextService
from housing_context.service import CurrentHomeLoanContextService
from input_logic.input_mapper import map_to_profile
from input_logic.validators import validate_raw_input
from output_logic.report_builder import bundle_to_dict
from output_logic.source_report_builder import build_source_report_text
from output_logic.sentence_builder import build_summary_text
from output_logic.table_builder import build_analysis_tables


DEFAULT_EXPENSE_CATEGORIES = {
    "food": 89.0,
    "transport": 30.0,
    "utilities": 30.0,
    "communication": 20.0,
    "housing": 69.0,
    "leisure": 21.0,
    "fashion": 21.0,
    "social": 22.0,
    "allowance": 39.0,
    "education": 97.0,
    "medical": 26.0,
}

DEFAULT_SAVING_PRODUCTS = {
    "cash_flow": 5.0,
    "installment": 0.0,
    "investment": 0.0,
    "pension_savings": 50.0,
    "irp": 25.0,
    "housing_subscription": 25.0,
}

DEFAULT_INSURANCE_PRODUCTS = {
    "indemnity_insurance": 1.0,
    "life_insurance": 1.0,
    "variable_insurance": 1.0,
}


class InputValidationError(ValueError):
    def __init__(self, errors: List[str]):
        self.errors = list(errors)
        message = "\n".join(self.errors) if self.errors else "입력값 검증에 실패했습니다."
        super().__init__(message)


@dataclass
class PlannerRunResult:
    raw_input: Dict[str, Any]
    normalized_input: Dict[str, Any]
    warnings: List[str]
    summary_text: str
    source_report_text: str
    comparison_tables: List[dict]
    report_payload: Dict[str, Any]
    report_json: str


@lru_cache(maxsize=1)
def _get_analysis_service() -> AnalysisService:
    return AnalysisService()


@lru_cache(maxsize=1)
def _build_default_template() -> Dict[str, Any]:
    economic_defaults = CurrentEconomicContextService().build_default_percent_map()
    home_defaults = CurrentHomeLoanContextService().build_default_input_map()
    pension_current_age = 45

    return {
        "name": "홍길동",
        "gender": "male",
        "birth_year": "",
        "birth_month": "",
        "birth_day": "",
        "age": pension_current_age,
        "marital_status": "married",
        "children_count": 1,
        "youngest_child_stage": "middle_high",
        "household_income": 628.0,
        "monthly_expense": 379.0,
        "monthly_debt_payment": 53.0,
        "monthly_saving_investment": 108.0,
        "monthly_emergency_fund": 88.0,
        "average_consumption": 379.0,
        "liquid_assets": 8055.0,
        "non_liquid_assets": 68962.0,
        "economic_assumptions": economic_defaults,
        "special_goals": [
            {
                "name": "주택자금",
                "target_amount": float(home_defaults["house_price"]),
                "target_years": int(home_defaults["target_years"]),
            },
            {
                "name": "교육자금",
                "target_amount": 5000.0,
                "target_years": 8,
            },
        ],
        "expense_categories": DEFAULT_EXPENSE_CATEGORIES,
        "saving_products": DEFAULT_SAVING_PRODUCTS,
        "insurance_products": DEFAULT_INSURANCE_PRODUCTS,
        "home_purchase_goal": home_defaults,
        "pension": {
            "current_age": pension_current_age,
            "retirement_age": 60,
            "expected_monthly_pension": 200.0,
            "current_balance": 3000.0,
        },
    }


def build_default_raw_input() -> Dict[str, Any]:
    return deepcopy(_build_default_template())


def run_financial_analysis(raw_input: Dict[str, Any]) -> PlannerRunResult:
    normalized, errors, warnings = validate_raw_input(raw_input)
    if errors:
        raise InputValidationError(errors)

    profile = map_to_profile(normalized)
    analysis = _get_analysis_service().analyze(profile, warnings=warnings)
    summary_text = build_summary_text(profile, analysis)
    source_report_text = build_source_report_text(profile, analysis)
    comparison_tables = build_analysis_tables(profile, analysis)
    report_payload = bundle_to_dict(profile, analysis)

    return PlannerRunResult(
        raw_input=deepcopy(raw_input),
        normalized_input=normalized,
        warnings=list(warnings),
        summary_text=summary_text,
        source_report_text=source_report_text,
        comparison_tables=comparison_tables,
        report_payload=report_payload,
        report_json=json.dumps(report_payload, ensure_ascii=False, indent=2),
    )
