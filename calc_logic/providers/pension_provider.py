from calc_logic.providers.base_provider import BaseBenchmarkProvider


class PensionBenchmarkProvider(BaseBenchmarkProvider):
    provider_name = "pension"

    def __init__(self, assumptions: dict):
        self.assumptions = assumptions

    @staticmethod
    def _real_rate(nominal: float, inflation: float) -> float:
        return ((1.0 + nominal) / (1.0 + inflation)) - 1.0

    @staticmethod
    def _growth_factor(rate: float, months: int) -> float:
        if months <= 0:
            return 1.0
        return (1.0 + rate) ** (months / 12.0)

    @staticmethod
    def _future_value_of_current_balance(balance: float, monthly_rate: float, months: int) -> float:
        if months <= 0:
            return balance
        if abs(monthly_rate) < 1e-9:
            return balance
        return balance * ((1.0 + monthly_rate) ** months)

    @staticmethod
    def _required_monthly_payment(target_fv: float, current_fv: float, monthly_rate: float, months: int) -> float:
        shortfall = max(target_fv - current_fv, 0.0)
        if months <= 0:
            return shortfall
        if abs(monthly_rate) < 1e-9:
            return shortfall / months
        factor = (((1.0 + monthly_rate) ** months) - 1.0) / monthly_rate
        if abs(factor) < 1e-9:
            return shortfall / months
        return shortfall / factor

    def calculate_required_monthly_contribution(self, pension_profile) -> dict:
        current_age = pension_profile.current_age
        retirement_age = max(pension_profile.retirement_age, current_age + 1)
        expected_monthly_pension = pension_profile.expected_monthly_pension
        current_balance = pension_profile.current_balance
        retirement_age_adjusted = retirement_age != pension_profile.retirement_age

        inflation_rate = self.assumptions["inflation_rate"]
        accumulation_nominal = self.assumptions["accumulation_return_rate"]
        payout_real = self._real_rate(
            self.assumptions["payout_return_rate"],
            inflation_rate,
        )

        months_to_retirement = max((retirement_age - current_age) * 12, 1)
        payout_months = max(int(self.assumptions["retirement_years"] * 12), 1)

        inflation_growth_to_retirement = self._growth_factor(inflation_rate, months_to_retirement)
        inflation_adjusted_monthly_pension = expected_monthly_pension * inflation_growth_to_retirement

        payout_monthly_rate = payout_real / 12.0
        if abs(payout_monthly_rate) < 1e-9:
            target_capital = inflation_adjusted_monthly_pension * payout_months
        else:
            target_capital = inflation_adjusted_monthly_pension * (
                (1.0 - ((1.0 + payout_monthly_rate) ** (-payout_months))) / payout_monthly_rate
            )

        accumulation_monthly_rate = accumulation_nominal / 12.0
        future_value_of_balance = self._future_value_of_current_balance(
            balance=current_balance,
            monthly_rate=accumulation_monthly_rate,
            months=months_to_retirement,
        )

        required_monthly = self._required_monthly_payment(
            target_fv=target_capital,
            current_fv=future_value_of_balance,
            monthly_rate=accumulation_monthly_rate,
            months=months_to_retirement,
        )

        return self.build_analysis_result(
            method="reverse_required_contribution_with_inflation",
            detail={
                "current_age": current_age,
                "requested_retirement_age": pension_profile.retirement_age,
                "applied_retirement_age": retirement_age,
                "retirement_age_adjusted": retirement_age_adjusted,
            },
            expected_monthly_pension_today_value=expected_monthly_pension,
            inflation_adjusted_monthly_pension_at_retirement=inflation_adjusted_monthly_pension,
            inflation_growth_to_retirement=inflation_growth_to_retirement,
            target_capital_at_retirement=target_capital,
            future_value_of_current_balance=future_value_of_balance,
            required_monthly_contribution=required_monthly,
            months_to_retirement=months_to_retirement,
            payout_months=payout_months,
            assumptions=self.assumptions,
        )
