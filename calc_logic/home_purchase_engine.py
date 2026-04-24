def _monthly_amortized_payment(principal: float, annual_interest_rate: float, months: int) -> float:
    if principal <= 0 or months <= 0:
        return 0.0
    monthly_rate = annual_interest_rate / 12.0
    if monthly_rate <= 0:
        return principal / months
    factor = (1.0 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1.0)


def calculate_home_purchase_plan(
    house_price: float,
    ltv: float,
    dti: float,
    target_years: int,
    loan_term_years: int,
    loan_interest_rate: float,
    household_income: float = 0.0,
) -> dict:
    safe_house_price = max(float(house_price or 0.0), 0.0)
    safe_ltv = min(max(float(ltv or 0.0), 0.0), 1.0)
    safe_dti = min(max(float(dti or 0.0), 0.0), 1.0)
    safe_target_years = max(int(target_years or 0), 0)
    safe_loan_term_years = max(int(loan_term_years or 0), 0)
    safe_loan_interest_rate = max(float(loan_interest_rate or 0.0), 0.0)

    down_payment_target = safe_house_price * (1.0 - safe_ltv)
    loan_amount = safe_house_price * safe_ltv
    saving_months = safe_target_years * 12
    loan_months = safe_loan_term_years * 12

    required_monthly_saving = 0.0 if saving_months <= 0 else down_payment_target / saving_months
    monthly_repayment = _monthly_amortized_payment(loan_amount, safe_loan_interest_rate, loan_months)
    dti_limit_payment = max(float(household_income or 0.0), 0.0) * safe_dti
    repayment_to_income_ratio = 0.0
    within_dti_limit = None

    if household_income and household_income > 0:
        repayment_to_income_ratio = monthly_repayment / household_income
        within_dti_limit = monthly_repayment <= dti_limit_payment

    return {
        "house_price": safe_house_price,
        "ltv": safe_ltv,
        "dti": safe_dti,
        "target_years": safe_target_years,
        "loan_term_years": safe_loan_term_years,
        "loan_interest_rate": safe_loan_interest_rate,
        "down_payment_target": down_payment_target,
        "loan_amount": loan_amount,
        "required_monthly_saving": required_monthly_saving,
        "monthly_repayment": monthly_repayment,
        "dti_limit_payment": dti_limit_payment,
        "repayment_to_income_ratio": repayment_to_income_ratio,
        "within_dti_limit": within_dti_limit,
    }
