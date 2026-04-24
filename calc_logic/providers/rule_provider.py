from calc_logic.providers.base_provider import BaseBenchmarkProvider


class RuleBenchmarkProvider(BaseBenchmarkProvider):
    provider_name = "rule"

    def get_emergency_fund_target(self, profile) -> dict:
        target_balance = profile.monthly_expense * 6.0
        months_cover = 0.0 if profile.monthly_expense <= 0 else profile.liquid_assets / profile.monthly_expense
        return self.build_analysis_result(
            method="expense_multiple",
            detail={
                "expense_basis": "monthly_expense",
                "target_months": 6,
            },
            target_balance=target_balance,
            current_balance=profile.liquid_assets,
            gap=profile.liquid_assets - target_balance,
            months_cover=months_cover,
        )
