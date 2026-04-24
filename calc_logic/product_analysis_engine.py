from typing import Dict

from models.analysis_models import (
    ProductComparison,
    SavingProductAnalysis,
    TaxBenefitProductAnalysis,
)


def classify_product_gap(gap_ratio: float) -> str:
    if gap_ratio <= -0.10:
        return "underweight"
    if gap_ratio >= 0.10:
        return "overweight"
    if abs(gap_ratio) <= 0.05:
        return "aligned"
    return "tilted"


def classify_concentration(actual_ratio: float, gap_ratio: float) -> str:
    if actual_ratio >= 0.55 or gap_ratio >= 0.15:
        return "high"
    if actual_ratio >= 0.40 or gap_ratio >= 0.08:
        return "moderate"
    return "low"


def build_product_narrative(product_key: str, status: str, concentration: str) -> str:
    focus_map = {
        "cash_flow": "유동성 확보",
        "installment": "목적자금 적립",
        "insurance": "보장 준비",
        "investment": "성장자산 배분",
    }
    focus = focus_map.get(product_key, "구성 비중")

    if concentration == "high":
        return f"{focus} 쪽으로 편중이 커 보여 비중 점검이 필요합니다."
    if status == "overweight":
        return f"{focus} 비중이 기준보다 높아 다른 상품과의 균형을 함께 보는 것이 좋습니다."
    if status == "underweight":
        return f"{focus} 비중이 기준보다 낮아 목표 기능이 충분한지 확인이 필요합니다."
    if status == "aligned":
        return f"{focus} 비중이 기준과 유사합니다."
    return f"{focus} 비중이 기준과 다소 차이 나므로 추이를 함께 보는 것이 좋습니다."


def _aggregate_products(
    actual_products: Dict[str, float],
    benchmark_product_labels: Dict[str, str],
    product_category_map: Dict[str, str],
) -> Dict[str, float]:
    aggregated = {product_key: 0.0 for product_key in benchmark_product_labels}
    for product_key, raw_amount in actual_products.items():
        benchmark_key = product_category_map.get(product_key)
        if benchmark_key not in aggregated:
            continue
        aggregated[benchmark_key] += float(raw_amount or 0.0)
    return aggregated


def _build_tax_credit_narrative(label: str, annual_amount: float, benefit_base_amount: float, benefit_min: float, benefit_max: float) -> str:
    if benefit_base_amount <= 0:
        return f"{label} 납입액이 없어 현재 반영되는 세액공제는 없습니다."
    if abs(benefit_min - benefit_max) < 1e-9:
        return (
            f"연간 {annual_amount:,.0f}만원 납입 중 {benefit_base_amount:,.0f}만원이 세액공제 대상이며, "
            f"예상 세액공제는 {benefit_max:,.1f}만원입니다."
        )
    return (
        f"연간 {annual_amount:,.0f}만원 납입 중 {benefit_base_amount:,.0f}만원이 세액공제 대상이며, "
        f"소득구간에 따라 예상 세액공제는 {benefit_min:,.1f}~{benefit_max:,.1f}만원입니다."
    )


def _build_income_deduction_narrative(label: str, annual_amount: float, benefit_base_amount: float, deduction_base_amount: float) -> str:
    if benefit_base_amount <= 0:
        return f"{label} 납입액이 없어 현재 반영되는 소득공제 대상액은 없습니다."
    return (
        f"연간 {annual_amount:,.0f}만원 납입 중 {benefit_base_amount:,.0f}만원 한도 기준으로 "
        f"{deduction_base_amount:,.1f}만원이 소득공제 대상입니다. 실제 절세액은 총급여와 무주택 요건 확인이 필요합니다."
    )


def _build_tax_benefit_products(
    actual_products: Dict[str, float],
    tax_benefit_payload: dict,
) -> Dict[str, TaxBenefitProductAnalysis]:
    rules = tax_benefit_payload.get("products", {})
    source = tax_benefit_payload.get("tax_source", tax_benefit_payload.get("source", "report"))
    detail_base = dict(tax_benefit_payload.get("detail", {}))
    combined_usage: Dict[str, float] = {}
    analyses: Dict[str, TaxBenefitProductAnalysis] = {}

    for product_key, rule in rules.items():
        monthly_amount = float(actual_products.get(product_key, 0.0) or 0.0)
        annual_amount = monthly_amount * 12.0
        if annual_amount <= 0:
            continue

        benefit_type = rule.get("benefit_type", "")
        annual_cap = float(rule.get("annual_cap", annual_amount))
        benefit_base_amount = min(annual_amount, annual_cap)

        combined_group = rule.get("combined_group")
        combined_cap = rule.get("combined_cap")
        if combined_group and combined_cap is not None:
            remaining_cap = max(0.0, float(combined_cap) - combined_usage.get(combined_group, 0.0))
            benefit_base_amount = min(benefit_base_amount, remaining_cap)
            combined_usage[combined_group] = combined_usage.get(combined_group, 0.0) + benefit_base_amount

        estimated_benefit_min = 0.0
        estimated_benefit_max = 0.0
        deduction_base_amount = 0.0

        if benefit_type == "tax_credit":
            rates = [float(rate) for rate in rule.get("rates", {}).values()]
            if rates:
                estimated_benefit_min = benefit_base_amount * min(rates)
                estimated_benefit_max = benefit_base_amount * max(rates)
            narrative = _build_tax_credit_narrative(
                rule.get("label", product_key),
                annual_amount,
                benefit_base_amount,
                estimated_benefit_min,
                estimated_benefit_max,
            )
            method = "tax_credit_cap_range"
        else:
            deduction_rate = float(rule.get("deduction_rate", 0.0))
            deduction_base_amount = benefit_base_amount * deduction_rate
            narrative = _build_income_deduction_narrative(
                rule.get("label", product_key),
                annual_amount,
                benefit_base_amount,
                deduction_base_amount,
            )
            method = "income_deduction_cap"

        analyses[product_key] = TaxBenefitProductAnalysis(
            product_key=product_key,
            label=rule.get("label", product_key),
            monthly_amount=monthly_amount,
            annual_amount=annual_amount,
            benefit_type=benefit_type,
            benefit_base_amount=benefit_base_amount,
            estimated_benefit_min=estimated_benefit_min,
            estimated_benefit_max=estimated_benefit_max,
            deduction_base_amount=deduction_base_amount,
            narrative=narrative,
            source=source,
            method=method,
            detail={
                **detail_base,
                "annual_cap": annual_cap,
                "combined_group": combined_group,
                "combined_cap": combined_cap,
                "rates": rule.get("rates", {}),
                "deduction_rate": rule.get("deduction_rate"),
                "eligibility": rule.get("eligibility", {}),
                "notes": rule.get("notes", ""),
                "source_page": rule.get("source_page"),
            },
        )

    return analyses


def analyze_saving_products(
    actual_products: Dict[str, float],
    monthly_saving_investment: float,
    benchmark_payload: dict,
    benchmark_product_labels: Dict[str, str],
    product_category_map: Dict[str, str],
    tax_benefit_payload: dict,
) -> SavingProductAnalysis:
    product_sum = sum(float(value) for value in actual_products.values())
    ratio_base_amount = float(monthly_saving_investment or product_sum or 0.0)
    benchmark_products = benchmark_payload.get("products", {})
    source = benchmark_payload.get("source", "")
    method = benchmark_payload.get("method", "")
    detail = dict(benchmark_payload.get("detail", {}))
    detail["ratio_base"] = "monthly_saving_investment" if monthly_saving_investment > 0 else "saving_product_sum"
    detail["saving_product_sum"] = product_sum

    aggregated_products = _aggregate_products(
        actual_products=actual_products,
        benchmark_product_labels=benchmark_product_labels,
        product_category_map=product_category_map,
    )
    detail["aggregated_products"] = aggregated_products

    comparisons: Dict[str, ProductComparison] = {}
    dominant_product_key = ""
    dominant_product_ratio = 0.0

    for product_key, label in benchmark_product_labels.items():
        actual_amount = float(aggregated_products.get(product_key, 0.0))
        actual_ratio = 0.0 if ratio_base_amount <= 0 else actual_amount / ratio_base_amount
        benchmark_entry = benchmark_products.get(product_key, {})
        benchmark_ratio = float(benchmark_entry.get("ratio", 0.0))
        benchmark_amount = ratio_base_amount * benchmark_ratio
        gap_amount = actual_amount - benchmark_amount
        gap_ratio = actual_ratio - benchmark_ratio
        status = classify_product_gap(gap_ratio)
        concentration = classify_concentration(actual_ratio, gap_ratio)

        if actual_ratio >= dominant_product_ratio:
            dominant_product_key = product_key
            dominant_product_ratio = actual_ratio

        comparisons[product_key] = ProductComparison(
            product_key=product_key,
            label=label,
            actual_amount=actual_amount,
            actual_ratio=actual_ratio,
            benchmark_amount=benchmark_amount,
            benchmark_ratio=benchmark_ratio,
            gap_amount=gap_amount,
            gap_ratio=gap_ratio,
            status=status,
            concentration=concentration,
            narrative=build_product_narrative(product_key, status, concentration),
            source=source,
            method=method,
            detail={
                **detail,
                "product_key": product_key,
                "benchmark_amount": benchmark_entry.get("amount"),
            },
        )

    dominant_comparison = comparisons.get(dominant_product_key)
    concentration_risk = dominant_comparison.concentration if dominant_comparison else "low"

    tax_benefit_products = _build_tax_benefit_products(actual_products, tax_benefit_payload)
    total_estimated_tax_benefit_min = sum(item.estimated_benefit_min for item in tax_benefit_products.values())
    total_estimated_tax_benefit_max = sum(item.estimated_benefit_max for item in tax_benefit_products.values())
    total_deduction_base_amount = sum(item.deduction_base_amount for item in tax_benefit_products.values())

    return SavingProductAnalysis(
        total_input_amount=product_sum,
        ratio_base_amount=ratio_base_amount,
        dominant_product_key=dominant_product_key,
        dominant_product_ratio=dominant_product_ratio,
        concentration_risk=concentration_risk,
        source=source,
        method=method,
        product_comparisons=comparisons,
        aggregated_products=aggregated_products,
        tax_benefit_products=tax_benefit_products,
        total_estimated_tax_benefit_min=total_estimated_tax_benefit_min,
        total_estimated_tax_benefit_max=total_estimated_tax_benefit_max,
        total_deduction_base_amount=total_deduction_base_amount,
        detail=detail,
    )
