from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BenchmarkSelection:
    group_id: int
    group_title: str
    band_key: str
    band_income: float
    fallback_note: str = ""
    band_min_income: Optional[float] = None
    band_max_income: Optional[float] = None
    selection_method: str = "nearest_average"
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class MetricComparison:
    metric_name: str
    label: str
    actual_value: float
    benchmark_value: float
    gap: float
    gap_rate: float
    status: str
    source: str
    method: str
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class CategoryComparison:
    category_key: str
    label: str
    actual_value: float
    benchmark_value: float
    gap: float
    gap_rate: float
    status: str
    fixed_spend_rate: Optional[float] = None
    source: str = ""
    method: str = ""
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class IncomeAllocationComparison:
    flow_key: str
    label: str
    actual_amount: float
    benchmark_amount: float
    actual_ratio: float
    benchmark_ratio: float
    amount_gap: float
    ratio_gap: float
    ratio_gap_rate: float
    status: str
    source: str = ""
    method: str = ""
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class DominantExpenseAnalysis:
    category_key: str
    label: str
    benchmark_amount: float
    benchmark_fixed_spend_rate: Optional[float]
    actual_amount: float
    actual_gap: float
    actual_gap_rate: float
    actual_top_category_key: str
    actual_top_label: str
    actual_top_amount: float
    matches_actual_top: bool
    source: str = ""
    method: str = ""
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class ProductComparison:
    product_key: str
    label: str
    actual_amount: float
    actual_ratio: float
    benchmark_amount: float
    benchmark_ratio: float
    gap_amount: float
    gap_ratio: float
    status: str
    concentration: str
    narrative: str
    source: str
    method: str
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class TaxBenefitProductAnalysis:
    product_key: str
    label: str
    monthly_amount: float
    annual_amount: float
    benefit_type: str
    benefit_base_amount: float
    estimated_benefit_min: float
    estimated_benefit_max: float
    deduction_base_amount: float
    narrative: str
    source: str
    method: str
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class SavingProductAnalysis:
    total_input_amount: float
    ratio_base_amount: float
    dominant_product_key: str
    dominant_product_ratio: float
    concentration_risk: str
    source: str
    method: str
    product_comparisons: Dict[str, ProductComparison]
    aggregated_products: Dict[str, float] = field(default_factory=dict)
    tax_benefit_products: Dict[str, TaxBenefitProductAnalysis] = field(default_factory=dict)
    total_estimated_tax_benefit_min: float = 0.0
    total_estimated_tax_benefit_max: float = 0.0
    total_deduction_base_amount: float = 0.0
    detail: Dict[str, object] = field(default_factory=dict)


@dataclass
class AnalysisBundle:
    benchmark_selection: BenchmarkSelection
    warnings: List[str]
    metric_comparisons: Dict[str, MetricComparison]
    category_comparisons: Dict[str, CategoryComparison]
    pension_result: Dict[str, object]
    emergency_rule_result: Dict[str, object]
    saving_product_analysis: SavingProductAnalysis
    home_purchase_result: Dict[str, object]
    raw_context: Dict[str, object]
    income_allocation_comparisons: Dict[str, IncomeAllocationComparison] = field(default_factory=dict)
    dominant_expense_analysis: Optional[DominantExpenseAnalysis] = None
    external_benchmark_summary: Dict[str, object] = field(default_factory=dict)
    economic_context_summary: Dict[str, object] = field(default_factory=dict)
