from __future__ import annotations

import streamlit as st

from core import InputValidationError, build_default_raw_input, run_financial_analysis


st.set_page_config(page_title="Financial Analysis", layout="wide")


GENDER_OPTIONS = {
    "male": "남성",
    "female": "여성",
}

MARITAL_STATUS_OPTIONS = {
    "single": "미혼",
    "married": "기혼",
}

CHILD_STAGE_OPTIONS = {
    "none": "해당 없음",
    "preschool": "미취학",
    "elementary": "초등",
    "middle_high": "중고등",
    "college": "대학생",
    "adult": "성인",
}

EXPENSE_CATEGORY_FIELDS = [
    ("food", "식비"),
    ("transport", "교통비"),
    ("utilities", "공과금"),
    ("communication", "통신비"),
    ("housing", "주거비"),
    ("leisure", "여가/취미"),
    ("fashion", "패션/미용"),
    ("social", "모임/경조사"),
    ("allowance", "용돈"),
    ("education", "교육비"),
    ("medical", "의료비"),
]

SAVING_PRODUCT_FIELDS = [
    ("cash_flow", "CMA/현금성"),
    ("installment", "예적금"),
    ("investment", "투자상품"),
    ("pension_savings", "연금저축"),
    ("irp", "IRP"),
    ("housing_subscription", "주택청약"),
]

INSURANCE_FIELDS = [
    ("indemnity_insurance", "실손보험"),
    ("life_insurance", "생명보험"),
    ("variable_insurance", "변액보험"),
]

ECONOMIC_FIELDS = [
    ("inflation_rate", "물가상승률 (%)"),
    ("investment_return_rate", "투자수익률 (%)"),
    ("installment_return_rate", "예적금수익률 (%)"),
    ("pension_accumulation_return_rate", "연금 적립 수익률 (%)"),
    ("pension_payout_return_rate", "연금 수령 수익률 (%)"),
]


def _format_choice(options: dict[str, str], key: str) -> str:
    return options.get(key, key)


def _render_money_inputs(fields: list[tuple[str, str]], values: dict, key_prefix: str):
    rendered = {}
    columns = st.columns(2)
    for index, (field_key, label) in enumerate(fields):
        column = columns[index % 2]
        rendered[field_key] = column.number_input(
            label,
            min_value=0.0,
            value=float(values.get(field_key, 0.0)),
            step=1.0,
            key=f"{key_prefix}_{field_key}",
        )
    return rendered


def _table_to_rows(table: dict) -> list[dict]:
    rows = []
    for row in table.get("rows", []):
        values = dict(row.get("values", {}))
        values["판정색"] = row.get("tone", "")
        rows.append(values)
    return rows


def _build_form_payload(defaults: dict) -> dict:
    with st.form("financial_analysis_form"):
        st.subheader("기본 정보")
        identity_col1, identity_col2, identity_col3 = st.columns(3)
        name = identity_col1.text_input("이름", value=str(defaults["name"]))
        gender = identity_col2.selectbox(
            "성별",
            options=list(GENDER_OPTIONS),
            index=list(GENDER_OPTIONS).index(defaults["gender"]),
            format_func=lambda value: _format_choice(GENDER_OPTIONS, value),
        )
        age = identity_col3.number_input("나이", min_value=20, max_value=100, value=int(defaults["age"]), step=1)

        family_col1, family_col2, family_col3 = st.columns(3)
        marital_status = family_col1.selectbox(
            "혼인 상태",
            options=list(MARITAL_STATUS_OPTIONS),
            index=list(MARITAL_STATUS_OPTIONS).index(defaults["marital_status"]),
            format_func=lambda value: _format_choice(MARITAL_STATUS_OPTIONS, value),
        )
        children_count = family_col2.number_input(
            "자녀 수",
            min_value=0,
            max_value=10,
            value=int(defaults["children_count"]),
            step=1,
        )
        youngest_child_stage = family_col3.selectbox(
            "막내 자녀 단계",
            options=list(CHILD_STAGE_OPTIONS),
            index=list(CHILD_STAGE_OPTIONS).index(defaults["youngest_child_stage"]),
            format_func=lambda value: _format_choice(CHILD_STAGE_OPTIONS, value),
        )

        st.subheader("재무 입력")
        finance_col1, finance_col2, finance_col3, finance_col4 = st.columns(4)
        household_income = finance_col1.number_input(
            "월 가구소득 (만원)",
            min_value=0.0,
            value=float(defaults["household_income"]),
            step=1.0,
        )
        monthly_expense = finance_col2.number_input(
            "월 생활비/지출 (만원)",
            min_value=0.0,
            value=float(defaults["monthly_expense"]),
            step=1.0,
        )
        monthly_debt_payment = finance_col3.number_input(
            "월 부채상환액 (만원)",
            min_value=0.0,
            value=float(defaults["monthly_debt_payment"]),
            step=1.0,
        )
        monthly_saving_investment = finance_col4.number_input(
            "월 저축/투자액 (만원)",
            min_value=0.0,
            value=float(defaults["monthly_saving_investment"]),
            step=1.0,
        )

        asset_col1, asset_col2, asset_col3, asset_col4 = st.columns(4)
        monthly_emergency_fund = asset_col1.number_input(
            "월 비상자금 (만원)",
            min_value=0.0,
            value=float(defaults["monthly_emergency_fund"]),
            step=1.0,
        )
        average_consumption = asset_col2.number_input(
            "평균 소비액 (만원)",
            min_value=0.0,
            value=float(defaults["average_consumption"]),
            step=1.0,
        )
        liquid_assets = asset_col3.number_input(
            "금융자산 (만원)",
            min_value=0.0,
            value=float(defaults["liquid_assets"]),
            step=1.0,
        )
        non_liquid_assets = asset_col4.number_input(
            "비금융자산 (만원)",
            min_value=0.0,
            value=float(defaults["non_liquid_assets"]),
            step=1.0,
        )

        with st.expander("경제 가정", expanded=False):
            economic_assumptions = {}
            economic_columns = st.columns(2)
            for index, (field_key, label) in enumerate(ECONOMIC_FIELDS):
                column = economic_columns[index % 2]
                economic_assumptions[field_key] = column.number_input(
                    label,
                    min_value=0.0,
                    value=float(defaults["economic_assumptions"][field_key]),
                    step=0.1,
                    key=f"economic_{field_key}",
                )

        with st.expander("지출 세부 항목", expanded=False):
            expense_categories = _render_money_inputs(
                EXPENSE_CATEGORY_FIELDS,
                defaults["expense_categories"],
                "expense",
            )

        with st.expander("저축/투자 상품", expanded=False):
            saving_products = _render_money_inputs(
                SAVING_PRODUCT_FIELDS,
                defaults["saving_products"],
                "saving",
            )

        with st.expander("보험 구성", expanded=False):
            insurance_products = _render_money_inputs(
                INSURANCE_FIELDS,
                defaults["insurance_products"],
                "insurance",
            )

        with st.expander("주택 마련 목표", expanded=False):
            home = defaults["home_purchase_goal"]
            home_col1, home_col2, home_col3 = st.columns(3)
            house_price = home_col1.number_input(
                "주택 가격 (만원)",
                min_value=0.0,
                value=float(home["house_price"]),
                step=100.0,
            )
            ltv = home_col2.number_input(
                "LTV (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(home["ltv"]),
                step=1.0,
            )
            dti = home_col3.number_input(
                "DTI (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(home["dti"]),
                step=1.0,
            )

            home_col4, home_col5, home_col6 = st.columns(3)
            target_years = home_col4.number_input(
                "목표 기간 (년)",
                min_value=1,
                max_value=40,
                value=int(home["target_years"]),
                step=1,
            )
            loan_term_years = home_col5.number_input(
                "대출 기간 (년)",
                min_value=1,
                max_value=40,
                value=int(home["loan_term_years"]),
                step=1,
            )
            loan_interest_rate = home_col6.number_input(
                "대출 금리 (%)",
                min_value=0.0,
                value=float(home["loan_interest_rate"]),
                step=0.1,
            )

        with st.expander("연금 입력", expanded=False):
            pension = defaults["pension"]
            pension_col1, pension_col2, pension_col3, pension_col4 = st.columns(4)
            pension_current_age = pension_col1.number_input(
                "현재 나이",
                min_value=20,
                max_value=100,
                value=int(pension["current_age"]),
                step=1,
            )
            retirement_age = pension_col2.number_input(
                "은퇴 나이",
                min_value=30,
                max_value=100,
                value=int(pension["retirement_age"]),
                step=1,
            )
            expected_monthly_pension = pension_col3.number_input(
                "목표 연금액 (만원)",
                min_value=0.0,
                value=float(pension["expected_monthly_pension"]),
                step=1.0,
            )
            current_balance = pension_col4.number_input(
                "현재 적립액 (만원)",
                min_value=0.0,
                value=float(pension["current_balance"]),
                step=100.0,
            )

        with st.expander("추가 목표자금", expanded=False):
            goal = defaults["special_goals"][1]
            goal_col1, goal_col2, goal_col3 = st.columns(3)
            goal_name = goal_col1.text_input("추가 목표명", value=str(goal["name"]))
            goal_amount = goal_col2.number_input(
                "추가 목표금액 (만원)",
                min_value=0.0,
                value=float(goal["target_amount"]),
                step=100.0,
            )
            goal_years = goal_col3.number_input(
                "추가 목표 기간 (년)",
                min_value=1,
                max_value=40,
                value=int(goal["target_years"]),
                step=1,
            )

        submitted = st.form_submit_button("분석 실행", use_container_width=True, type="primary")

    special_goals = [
        {
            "name": "주택자금",
            "target_amount": house_price,
            "target_years": target_years,
        }
    ]
    if goal_name.strip() or goal_amount > 0:
        special_goals.append(
            {
                "name": goal_name.strip(),
                "target_amount": goal_amount,
                "target_years": goal_years,
            }
        )

    payload = {
        "name": name,
        "gender": gender,
        "birth_year": "",
        "birth_month": "",
        "birth_day": "",
        "age": age,
        "marital_status": marital_status,
        "children_count": children_count,
        "youngest_child_stage": youngest_child_stage,
        "household_income": household_income,
        "monthly_expense": monthly_expense,
        "monthly_debt_payment": monthly_debt_payment,
        "monthly_saving_investment": monthly_saving_investment,
        "monthly_emergency_fund": monthly_emergency_fund,
        "average_consumption": average_consumption,
        "liquid_assets": liquid_assets,
        "non_liquid_assets": non_liquid_assets,
        "economic_assumptions": economic_assumptions,
        "special_goals": special_goals,
        "expense_categories": expense_categories,
        "saving_products": saving_products,
        "insurance_products": insurance_products,
        "home_purchase_goal": {
            "house_price": house_price,
            "ltv": ltv,
            "dti": dti,
            "target_years": target_years,
            "loan_term_years": loan_term_years,
            "loan_interest_rate": loan_interest_rate,
        },
        "pension": {
            "current_age": pension_current_age,
            "retirement_age": retirement_age,
            "expected_monthly_pension": expected_monthly_pension,
            "current_balance": current_balance,
        },
    }
    return submitted, payload


def main():
    st.title("가계 재무 분석")
    st.caption("Tkinter 데스크톱 UI는 유지하고, 이 파일은 Streamlit Cloud 배포 전용 진입점으로 분리했습니다.")

    defaults = build_default_raw_input()
    submitted, raw_input = _build_form_payload(defaults)

    if submitted:
        try:
            st.session_state["analysis_result"] = run_financial_analysis(raw_input)
            st.session_state["analysis_errors"] = []
        except InputValidationError as exc:
            st.session_state["analysis_result"] = None
            st.session_state["analysis_errors"] = list(exc.errors)

    for error in st.session_state.get("analysis_errors", []):
        st.error(error)

    result = st.session_state.get("analysis_result")
    if not result:
        st.info("기본 입력값을 확인한 뒤 `분석 실행`을 누르면 결과가 여기에 표시됩니다.")
        return

    st.subheader("분석 결과")
    for warning in result.warnings:
        st.warning(warning)

    summary_tab, table_tab, source_tab, json_tab = st.tabs(
        ["요약", "비교표", "근거", "JSON"]
    )

    with summary_tab:
        st.text_area(
            "분석 요약",
            value=result.summary_text,
            height=420,
        )

    with table_tab:
        for table in result.comparison_tables:
            st.markdown(f"#### {table.get('title', '')}")
            description = (table.get("description") or "").strip()
            if description:
                st.caption(description)
            st.dataframe(_table_to_rows(table), use_container_width=True, hide_index=True)

    with source_tab:
        st.text_area(
            "분석 근거",
            value=result.source_report_text,
            height=420,
        )

    with json_tab:
        st.download_button(
            "결과 JSON 다운로드",
            data=result.report_json.encode("utf-8"),
            file_name="financial_analysis_report.json",
            mime="application/json",
        )
        st.json(result.report_payload)


if __name__ == "__main__":
    main()
