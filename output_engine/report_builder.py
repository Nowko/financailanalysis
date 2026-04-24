def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_summary_text(household_input, analysis_result) -> str:
    income = analysis_result.income_position
    assets = analysis_result.asset_position
    debt = analysis_result.debt_risk_level
    spending = analysis_result.spending_gap
    profile = analysis_result.household_profile_summary

    lines = [
        f"{profile['household_size']}인 가구 / {profile['age_band']} 기준 요약",
        (
            f"- 월소득은 중위소득 대비 {_pct(income['vs_median_income_ratio'])}, "
            f"동일 조건 평균 대비 {_pct(income['vs_peer_income_ratio'])}입니다."
        ),
        f"- 총자산은 비교 기준 대비 {_pct(assets['vs_peer_total_assets_ratio'])} 수준입니다.",
        (
            f"- 총부채는 자산 대비 {_pct(debt['debt_to_assets_ratio'])}이며, "
            f"부채 위험도는 {debt['level']}입니다."
        ),
        f"- 월소비지출은 비교 기준 대비 {_pct(spending['vs_peer_consumption_ratio'])} 수준입니다.",
        f"- 월 가처분 잉여는 {profile['monthly_surplus']:,.1f}만원입니다.",
    ]
    if analysis_result.notes:
        lines.append("- 참고: " + " / ".join(analysis_result.notes))
    return "\n".join(lines)


def build_output_payload(household_input, benchmark_context, analysis_result) -> dict:
    summary_text = build_summary_text(household_input, analysis_result)
    return {
        "input": household_input.to_dict(),
        "benchmarks": benchmark_context.to_dict(),
        "analysis": analysis_result.to_dict(),
        "summary_text": summary_text,
    }
