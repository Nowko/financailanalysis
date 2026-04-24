from pathlib import Path

from calc_logic.economic_assumption_registry import DEFAULT_ECONOMIC_ASSUMPTIONS


BASE_DIR = Path(__file__).resolve().parent
REPORT_BENCHMARK_FILE = BASE_DIR / "data" / "report_benchmarks" / "shinhan_ordinary_2024.json"

DEFAULT_PENSION_ASSUMPTIONS = {
    "accumulation_return_rate": 0.04,
    "inflation_rate": 0.02,
    "retirement_years": 25,
    "payout_return_rate": 0.02,
}

DEFAULT_HOME_PURCHASE_GOAL = {
    "house_price": 50000.0,
    "ltv": 0.70,
    "dti": 0.40,
    "target_years": 10,
    "loan_term_years": 30,
    "loan_interest_rate": 0.04,
}

CATEGORY_LABELS = {
    "food": "식비",
    "transport": "교통비",
    "utilities": "공과금",
    "communication": "통신비",
    "housing": "주거비",
    "leisure": "여가/취미",
    "fashion": "패션/미용",
    "social": "모임/경조사",
    "allowance": "용돈",
    "education": "교육비",
    "medical": "의료비",
}

EXPENSE_DETAIL_LABELS = {
    "food": {
        "daily_food": "일간 식비",
        "weekly_food": "주간 식비",
        "delivery_food": "배달 식비",
        "snacks": "간식",
        "coffee": "커피",
    },
    "transport": {
        "daily_bus": "일간 버스비",
        "daily_subway": "일간 전철비",
        "taxi": "택시비",
        "fuel": "기름값",
    },
    "utilities": {
        "electricity": "전기요금",
        "gas": "가스요금",
        "water": "수도세",
    },
    "communication": {
        "internet": "인터넷",
        "mobile": "모바일",
        "ott": "OTT",
    },
    "housing": {
        "monthly_rent": "월세",
        "principal_interest": "원리금",
    },
    "leisure": {
        "classes": "학원",
        "materials": "재료",
        "supplies": "소모품",
    },
    "fashion": {
        "clothing": "의류",
        "beauty": "미용",
        "hair": "헤어",
    },
    "social": {
        "meetings": "모임",
        "family_events": "경조사",
    },
    "allowance": {
        "personal_allowance": "개인 용돈",
        "family_support": "가족 지원",
    },
    "education": {
        "academy": "학원",
        "materials": "교재",
    },
    "medical": {
        "hospital": "병원",
        "medicine": "약값",
        "wellness": "건강관리",
    },
}

BENCHMARK_PRODUCT_LABELS = {
    "cash_flow": "수시입출금/CMA",
    "installment": "적금/청약",
    "insurance": "보험",
    "investment": "투자상품",
}

GENERAL_PRODUCT_LABELS = {
    "cash_flow": "수시입출금/CMA",
    "installment": "적금/청약",
    "investment": "투자상품",
}

TAX_BENEFIT_PRODUCT_LABELS = {
    "pension_savings": "연금저축",
    "irp": "IRP",
    "housing_subscription": "주택청약종합저축",
}

INSURANCE_PRODUCT_LABELS = {
    "indemnity_insurance": "실손",
    "life_insurance": "생보",
    "variable_insurance": "변액",
}

PRODUCT_LABELS = {
    **GENERAL_PRODUCT_LABELS,
    **TAX_BENEFIT_PRODUCT_LABELS,
    **INSURANCE_PRODUCT_LABELS,
    "insurance": "보험(통합)",
}

PRODUCT_INPUT_GROUPS = {
    "general": ("cash_flow", "installment", "investment"),
    "tax_benefit": ("pension_savings", "irp", "housing_subscription"),
    "insurance": ("indemnity_insurance", "life_insurance", "variable_insurance"),
}

EXPENSE_ALLOCATION_ORDER = (
    "cash_flow",
    "installment",
    "investment",
    "pension_savings",
    "irp",
    "housing_subscription",
    "indemnity_insurance",
    "life_insurance",
    "variable_insurance",
)

PRODUCT_BENCHMARK_CATEGORY_MAP = {
    "cash_flow": "cash_flow",
    "installment": "installment",
    "investment": "investment",
    "pension_savings": "investment",
    "irp": "investment",
    "housing_subscription": "installment",
    "insurance": "insurance",
    "indemnity_insurance": "insurance",
    "life_insurance": "insurance",
    "variable_insurance": "insurance",
}

EXPENSE_DETAIL_LABELS = {
    **EXPENSE_DETAIL_LABELS,
    "food": {
        "daily_food": EXPENSE_DETAIL_LABELS["food"]["daily_food"],
        "delivery_food": EXPENSE_DETAIL_LABELS["food"]["delivery_food"],
        "snacks": EXPENSE_DETAIL_LABELS["food"]["snacks"],
        "coffee": EXPENSE_DETAIL_LABELS["food"]["coffee"],
    },
}

EXPENSE_DETAIL_MULTIPLIERS = {
    "food": {
        "daily_food": 30.0,
    },
    "transport": {
        "daily_bus": 30.0,
        "daily_subway": 30.0,
    },
}

CATEGORY_LABELS = {
    **CATEGORY_LABELS,
    "housing": "주거비(월세성)",
}

EXPENSE_DETAIL_LABELS = {
    **EXPENSE_DETAIL_LABELS,
    "housing": {
        "monthly_rent": "월세",
        "principal_interest": "관리비",
    },
}
