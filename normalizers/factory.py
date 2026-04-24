from normalizers.document_source_normalizer import DocumentSourceNormalizer
from normalizers.kosis_household_normalizer import KosisHouseholdSurveyNormalizer
from normalizers.median_income_normalizer import MedianIncomeNormalizer


NORMALIZER_MAP = {
    KosisHouseholdSurveyNormalizer.normalizer_key: KosisHouseholdSurveyNormalizer,
    MedianIncomeNormalizer.normalizer_key: MedianIncomeNormalizer,
    DocumentSourceNormalizer.normalizer_key: DocumentSourceNormalizer,
}


def get_normalizer(normalizer_key: str):
    if normalizer_key not in NORMALIZER_MAP:
        raise KeyError(f"Unknown normalizer: {normalizer_key}")
    return NORMALIZER_MAP[normalizer_key]()
