import sys
import unittest
from datetime import datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.analysis_service import AnalysisService
from input_logic.input_mapper import map_to_profile
from input_logic.validators import validate_raw_input
from output_logic.word_report_builder import build_word_report_bytes, write_word_report


def _build_sample_profile_and_analysis():
    raw = {
        "name": "Tester",
        "gender": "male",
        "birth_year": "",
        "birth_month": "",
        "birth_day": "",
        "age": "45",
        "marital_status": "married",
        "children_count": "1",
        "youngest_child_stage": "middle_high",
        "household_income": "628",
        "monthly_expense": "379",
        "monthly_debt_payment": "53",
        "monthly_saving_investment": "108",
        "monthly_emergency_fund": "88",
        "average_consumption": "379",
        "liquid_assets": "8055",
        "non_liquid_assets": "68962",
        "economic_assumptions": {
            "inflation_rate": "2.0",
            "investment_return_rate": "4.0",
            "installment_return_rate": "3.0",
            "pension_accumulation_return_rate": "4.0",
            "pension_payout_return_rate": "2.0",
        },
        "special_goals": [
            {"name": "주택자금", "target_amount": "50000", "target_years": "10"},
        ],
        "expense_categories": {
            "food": "89",
            "transport": "30",
            "utilities": "30",
            "communication": "20",
            "housing": "69",
            "leisure": "21",
            "fashion": "21",
            "social": "22",
            "allowance": "39",
            "education": "97",
            "medical": "26",
        },
        "expense_detail_categories": {},
        "saving_products": {
            "cash_flow": "5",
            "installment": "0",
            "investment": "0",
            "pension_savings": "50",
            "irp": "25",
            "housing_subscription": "25",
        },
        "insurance_products": {
            "indemnity_insurance": "1",
            "life_insurance": "1",
            "variable_insurance": "1",
        },
        "home_purchase_goal": {
            "house_price": "50,000",
            "ltv": "70",
            "dti": "40",
            "target_years": "10",
            "loan_term_years": "30",
            "loan_interest_rate": "4.0",
        },
        "pension": {
            "current_age": "45",
            "retirement_age": "60",
            "expected_monthly_pension": "200",
            "current_balance": "3000",
        },
    }

    normalized, errors, warnings = validate_raw_input(raw)
    if errors:
        raise AssertionError(errors)
    profile = map_to_profile(normalized)
    analysis = AnalysisService().analyze(profile, warnings)
    return profile, analysis


class WordReportBuilderTests(unittest.TestCase):
    def test_build_word_report_bytes_contains_summary_and_tables(self):
        profile, analysis = _build_sample_profile_and_analysis()

        report_bytes = build_word_report_bytes(
            profile,
            analysis,
            generated_at=datetime(2026, 4, 24, 14, 30),
        )

        with ZipFile(BytesIO(report_bytes)) as archive:
            entries = set(archive.namelist())
            self.assertIn("[Content_Types].xml", entries)
            self.assertIn("word/document.xml", entries)
            self.assertIn("docProps/core.xml", entries)

            document_xml = archive.read("word/document.xml").decode("utf-8")
            self.assertIn("Tester 재무분석 보고서", document_xml)
            self.assertIn("분석 요약", document_xml)
            self.assertIn("비교표", document_xml)
            self.assertIn("자료 근거", document_xml)

    def test_write_word_report_creates_docx_file(self):
        profile, analysis = _build_sample_profile_and_analysis()

        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "24_Tester.docx"
            write_word_report(target, profile, analysis, generated_at=datetime(2026, 4, 24, 14, 30))

            self.assertTrue(target.exists())
            self.assertGreater(target.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
