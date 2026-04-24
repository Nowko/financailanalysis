import json
from pathlib import Path
from typing import Dict, Tuple

from calc_logic.life_stage import determine_group
from calc_logic.providers.base_provider import BaseBenchmarkProvider


class ReportBenchmarkProvider(BaseBenchmarkProvider):
    provider_name = "report"
    supported_metrics = (
        "household_income",
        "expense",
        "debt_payment",
        "saving_investment",
        "emergency_fund",
        "total_assets",
        "financial_assets_proxy",
        "real_estate_assets_proxy",
        "debt_balance",
    )

    def __init__(self, benchmark_file: Path):
        with open(benchmark_file, "r", encoding="utf-8") as file:
            self.data = json.load(file)
        self.income_band_rules = self.data.get("income_band_rules", {})
        self.saving_product_benchmarks = self.data.get("saving_product_benchmarks", {})
        self.tax_benefit_products = self.data.get("tax_benefit_products", {})

    def select_group_and_band(self, profile) -> Dict[str, object]:
        group_id, fallback_note = determine_group(
            age=profile.age,
            marital_status=profile.marital_status,
            children_count=profile.children_count,
            youngest_child_stage=profile.youngest_child_stage,
        )
        group = self.data["groups"][str(group_id)]
        rule_payload = group.get("income_band_rules") or self.income_band_rules
        band_key, band_rule, selection_method = self._select_income_band(
            group["bands"],
            profile.household_income,
            rule_payload,
        )
        band = group["bands"][band_key]
        return {
            "group_id": group_id,
            "group_title": group["title"],
            "band_key": band_key,
            "band": band,
            "band_rule": band_rule,
            "selection_method": selection_method,
            "fallback_note": fallback_note,
        }

    @staticmethod
    def _normalize_band_rule(band_key: str, band_rule: dict) -> dict:
        min_income = band_rule.get("min")
        max_income = band_rule.get("max")
        return {
            "band_key": band_key,
            "label": band_rule.get("label", f"Band {band_key}"),
            "min": None if min_income is None else float(min_income),
            "max": None if max_income is None else float(max_income),
        }

    @classmethod
    def _select_by_cutoff(cls, band_rules: Dict[str, dict], income: float) -> Tuple[str, dict]:
        for band_key in sorted(band_rules.keys(), key=int):
            normalized_rule = cls._normalize_band_rule(band_key, band_rules[band_key])
            lower = normalized_rule["min"]
            upper = normalized_rule["max"]
            lower_ok = lower is None or income >= lower
            upper_ok = upper is None or income < upper
            if lower_ok and upper_ok:
                return band_key, normalized_rule
        return "", {}

    @staticmethod
    def _derive_midpoint_rules(bands: Dict[str, dict]) -> Dict[str, dict]:
        ordered = sorted(
            ((band_key, float(band["household_income"])) for band_key, band in bands.items()),
            key=lambda item: item[1],
        )
        derived_rules: Dict[str, dict] = {}
        for index, (band_key, band_income) in enumerate(ordered):
            lower = None if index == 0 else (ordered[index - 1][1] + band_income) / 2.0
            upper = None if index == len(ordered) - 1 else (band_income + ordered[index + 1][1]) / 2.0
            derived_rules[band_key] = {
                "label": f"Band {band_key}",
                "min": lower,
                "max": upper,
            }
        return derived_rules

    @classmethod
    def _select_income_band(cls, bands: Dict[str, dict], income: float, rule_payload: Dict[str, object] = None):
        rule_payload = rule_payload or {}
        explicit_rules = rule_payload.get("bands", {})
        if explicit_rules:
            band_key, band_rule = cls._select_by_cutoff(explicit_rules, income)
            if band_key:
                return band_key, band_rule, rule_payload.get("selection_method", "cutoff")

        derived_rules = cls._derive_midpoint_rules(bands)
        band_key, band_rule = cls._select_by_cutoff(derived_rules, income)
        if band_key:
            return band_key, band_rule, "derived_midpoint"

        closest_key = "1"
        smallest_gap = None
        for band_key, band in bands.items():
            gap = abs(float(band["household_income"]) - float(income))
            if smallest_gap is None or gap < smallest_gap:
                closest_key = band_key
                smallest_gap = gap
        fallback_rule = cls._normalize_band_rule(
            closest_key,
            {
                "label": f"Band {closest_key}",
                "min": None,
                "max": None,
            },
        )
        return closest_key, fallback_rule, "nearest_average"

    def get_metric(self, metric_name: str, selection: Dict[str, object], profile) -> dict:
        band = selection["band"]
        metric_map = {
            "household_income": ("월 가구소득", band["household_income"]),
            "expense": ("월 지출", band["expense"]),
            "debt_payment": ("월 부채상환", band["debt_payment"]),
            "saving_investment": ("월 저축·투자", band["saving_investment"]),
            "emergency_fund": ("월 예비자금", band["emergency_fund"]),
            "total_assets": ("총자산", band["total_assets"]),
            "financial_assets_proxy": ("금융자산 추정치", band["financial_assets"]),
            "real_estate_assets_proxy": ("비현금성 자산 추정치", band["real_estate_assets"]),
            "debt_balance": ("부채잔액", band["debt_balance"]),
        }
        label, value = metric_map[metric_name]
        detail = self._build_selection_detail(selection)
        detail["fallback_note"] = selection["fallback_note"]
        return self.build_metric_result(
            metric_name=metric_name,
            label=label,
            value=float(value),
            method="group_band_lookup",
            detail=detail,
        )

    def get_expense_categories(self, selection: Dict[str, object]) -> Dict[str, object]:
        band = selection["band"]
        return self.build_analysis_result(
            method="group_band_lookup",
            detail=self._build_selection_detail(selection),
            values=band.get("expense_categories", {}),
            fixed_rates=band.get("expense_category_fixed_rate", {}),
        )

    def get_income_allocation(self, selection: Dict[str, object]) -> Dict[str, object]:
        band = selection["band"]
        return self.build_analysis_result(
            method="group_band_lookup",
            detail=self._build_selection_detail(selection),
            flows={
                "expense": {
                    "label": "소비/지출",
                    "amount": float(band.get("expense", 0.0)),
                    "ratio": float(band.get("expense_ratio", 0.0)) / 100.0,
                },
                "debt_payment": {
                    "label": "부채상환",
                    "amount": float(band.get("debt_payment", 0.0)),
                    "ratio": float(band.get("debt_ratio", 0.0)) / 100.0,
                },
                "saving_investment": {
                    "label": "저축/투자",
                    "amount": float(band.get("saving_investment", 0.0)),
                    "ratio": float(band.get("saving_ratio", 0.0)) / 100.0,
                },
                "emergency_fund": {
                    "label": "예비자금",
                    "amount": float(band.get("emergency_fund", 0.0)),
                    "ratio": float(band.get("emergency_ratio", 0.0)) / 100.0,
                },
            },
        )

    def get_dominant_expense_category(self, selection: Dict[str, object]) -> Dict[str, object]:
        band = selection["band"]
        expense_categories = band.get("expense_categories", {})
        fixed_rates = band.get("expense_category_fixed_rate", {})
        if expense_categories:
            category_key, amount = max(
                expense_categories.items(),
                key=lambda item: float(item[1]),
            )
        else:
            category_key, amount = "", 0.0
        detail = self._build_selection_detail(selection)
        detail["note"] = "소득구간 내 매월 고정적/정기적으로 소비하고 있는 금액이 가장 큰 소비 항목"
        detail["amount_note"] = "각 소비 항목별 금액은 고정 소비를 하고 있는 응답자 기준 소비 금액 평균"
        return self.build_analysis_result(
            method="largest_fixed_regular_expense",
            detail=detail,
            category_key=category_key,
            amount=float(amount),
            fixed_spend_rate=fixed_rates.get(category_key),
        )

    def get_saving_product_benchmark(
        self,
        selection: Dict[str, object],
        benchmark_key: str = "monthly_flow_2023",
    ) -> Dict[str, object]:
        band = selection["band"]
        benchmark = (
            band.get("saving_product_benchmarks", {}).get(benchmark_key)
            or self.saving_product_benchmarks.get(benchmark_key, {})
        )
        detail = self._build_selection_detail(selection)
        detail["benchmark_key"] = benchmark_key
        detail["scope"] = benchmark.get("scope", "overall_households")
        detail["source_page"] = benchmark.get("source_page")
        return self.build_analysis_result(
            method=benchmark.get("method", "monthly_flow_ratio"),
            detail=detail,
            products=benchmark.get("products", {}),
        )

    def get_tax_benefit_rules(self) -> Dict[str, object]:
        source_info = self.tax_benefit_products.get("source", {})
        references = source_info.get("references", {})
        detail = {
            "references": references,
            "notes": source_info.get("notes", ""),
        }
        payload = self.build_analysis_result(
            method="external_tax_rule_lookup",
            detail=detail,
            products=self.tax_benefit_products.get("products", {}),
        )
        payload["tax_source"] = source_info.get("name", "국세청")
        return payload

    @staticmethod
    def _build_selection_detail(selection: Dict[str, object]) -> Dict[str, object]:
        return {
            "group_id": selection["group_id"],
            "group_title": selection["group_title"],
            "band_key": selection["band_key"],
            "band_income": selection["band"]["household_income"],
            "band_min_income": selection["band_rule"].get("min"),
            "band_max_income": selection["band_rule"].get("max"),
            "selection_method": selection["selection_method"],
        }
