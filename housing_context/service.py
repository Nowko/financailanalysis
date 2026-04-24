import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from config import DEFAULT_HOME_PURCHASE_GOAL
from housing_context.models import CurrentHomeLoanContext, CurrentHomeLoanParameter


CURRENT_HOME_LOAN_CONTEXT_FILE = (
    Path(__file__).resolve().parents[1] / "data" / "current_context" / "current_home_loan_context.json"
)


@lru_cache(maxsize=4)
def _load_context_from_path(path_str: str) -> CurrentHomeLoanContext:
    with open(path_str, "r", encoding="utf-8") as file:
        payload = json.load(file)

    parameters = {}
    for key, item in payload.get("parameters", {}).items():
        parameters[key] = CurrentHomeLoanParameter(
            key=key,
            label=item["label"],
            value=float(item["value"]),
            unit=item.get("unit", ""),
            as_of_date=item.get("as_of_date", ""),
            published_at=item.get("published_at", ""),
            source_name=item.get("source_name", ""),
            official_url=item.get("official_url", ""),
            method=item.get("method", ""),
            note=item.get("note", ""),
        )

    return CurrentHomeLoanContext(
        context_name=payload.get("context_name", "current_home_loan_context"),
        as_of_date=payload.get("as_of_date", ""),
        parameters=parameters,
        notes=list(payload.get("notes", [])),
    )


class CurrentHomeLoanContextService:
    def __init__(self, data_path: Path = None):
        self.data_path = Path(data_path or CURRENT_HOME_LOAN_CONTEXT_FILE)

    def load_context(self) -> CurrentHomeLoanContext:
        return _load_context_from_path(str(self.data_path))

    def get_recommended_defaults(self) -> Dict[str, float]:
        context = self.load_context()
        return {
            "house_price": DEFAULT_HOME_PURCHASE_GOAL["house_price"],
            "ltv": float(context.parameters.get("ltv").value if context.parameters.get("ltv") else DEFAULT_HOME_PURCHASE_GOAL["ltv"]),
            "dti": float(context.parameters.get("dti").value if context.parameters.get("dti") else DEFAULT_HOME_PURCHASE_GOAL["dti"]),
            "target_years": int(context.parameters.get("target_years").value if context.parameters.get("target_years") else DEFAULT_HOME_PURCHASE_GOAL["target_years"]),
            "loan_term_years": int(context.parameters.get("loan_term_years").value if context.parameters.get("loan_term_years") else DEFAULT_HOME_PURCHASE_GOAL["loan_term_years"]),
            "loan_interest_rate": float(
                context.parameters.get("loan_interest_rate").value
                if context.parameters.get("loan_interest_rate")
                else DEFAULT_HOME_PURCHASE_GOAL["loan_interest_rate"]
            ),
        }

    def build_default_input_map(self) -> Dict[str, float]:
        defaults = self.get_recommended_defaults()
        return {
            "house_price": defaults["house_price"],
            "ltv": defaults["ltv"] * 100.0,
            "dti": defaults["dti"] * 100.0,
            "target_years": defaults["target_years"],
            "loan_term_years": defaults["loan_term_years"],
            "loan_interest_rate": defaults["loan_interest_rate"] * 100.0,
        }

    def build_context_summary(self, applied_values=None) -> dict:
        context = self.load_context()
        recommended = self.get_recommended_defaults()
        applied_values = applied_values or recommended

        parameter_entries = []
        for key, parameter in context.parameters.items():
            if isinstance(applied_values, dict):
                applied_value = applied_values.get(key, recommended.get(key, parameter.value))
            else:
                applied_value = getattr(applied_values, key, recommended.get(key, parameter.value))
            parameter_entries.append(
                {
                    "key": key,
                    "label": parameter.label,
                    "recommended_value": recommended.get(key, parameter.value),
                    "applied_value": float(applied_value),
                    "unit": parameter.unit,
                    "source_name": parameter.source_name,
                    "official_url": parameter.official_url,
                    "method": parameter.method,
                    "note": parameter.note,
                }
            )

        return {
            "context_name": context.context_name,
            "as_of_date": context.as_of_date,
            "parameters": {key: parameter.to_dict() for key, parameter in context.parameters.items()},
            "notes": list(context.notes),
            "recommended_defaults": recommended,
            "parameter_entries": parameter_entries,
        }

    def build_ui_hint(self) -> str:
        context = self.load_context()
        defaults = self.get_recommended_defaults()
        return (
            f"기준일 {context.as_of_date} / "
            f"LTV {defaults['ltv'] * 100:.0f}% / "
            f"DTI {defaults['dti'] * 100:.0f}% / "
            f"대출기간 {defaults['loan_term_years']}년 / "
            f"이자율 {defaults['loan_interest_rate'] * 100:.2f}%"
        )
