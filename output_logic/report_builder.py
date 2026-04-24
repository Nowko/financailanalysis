import json
from dataclasses import asdict, is_dataclass

from output_logic.diagnosis_builder import build_structured_insights
from output_logic.source_report_builder import build_source_report_payload
from output_logic.table_builder import build_analysis_tables


def bundle_to_dict(profile, analysis) -> dict:
    def convert(value):
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    return {
        "profile": profile.to_dict(),
        "analysis": {
            "benchmark_selection": convert(analysis.benchmark_selection),
            "warnings": analysis.warnings,
            "metric_comparisons": {key: convert(value) for key, value in analysis.metric_comparisons.items()},
            "category_comparisons": {key: convert(value) for key, value in analysis.category_comparisons.items()},
            "income_allocation_comparisons": {
                key: convert(value) for key, value in analysis.income_allocation_comparisons.items()
            },
            "dominant_expense_analysis": convert(analysis.dominant_expense_analysis),
            "pension_result": convert(analysis.pension_result),
            "emergency_rule_result": convert(analysis.emergency_rule_result),
            "saving_product_analysis": convert(analysis.saving_product_analysis),
            "home_purchase_result": convert(analysis.home_purchase_result),
            "raw_context": analysis.raw_context,
            "external_benchmark_summary": convert(analysis.external_benchmark_summary),
            "economic_context_summary": convert(analysis.economic_context_summary),
            "insights": build_structured_insights(profile, analysis),
            "comparison_tables": build_analysis_tables(profile, analysis),
            "source_report": build_source_report_payload(profile, analysis),
        },
    }


def dumps_report(profile, analysis) -> str:
    return json.dumps(bundle_to_dict(profile, analysis), ensure_ascii=False, indent=2)
