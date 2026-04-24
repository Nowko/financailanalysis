from typing import Tuple


def determine_group(age: int, marital_status: str, children_count: int, youngest_child_stage: str) -> Tuple[int, str]:
    marital_status = (marital_status or "single").lower()
    youngest_child_stage = (youngest_child_stage or "none").lower()

    if 60 <= age <= 64:
        return 9, ""

    if marital_status == "single":
        if 20 <= age <= 29:
            return 1, ""
        if 30 <= age <= 49:
            return 2, ""
        if age >= 50:
            return 2, "보고서에 50대 미혼 그룹이 없어 3040대 미혼 그룹으로 비교했습니다."
        return 1, "보고서 범위를 벗어나 20대 미혼 그룹으로 임시 비교했습니다."

    if children_count <= 0 or youngest_child_stage == "none":
        if 20 <= age <= 49:
            return 3, ""
        if age >= 50:
            return 3, "보고서에 50대 기혼 무자녀 그룹이 없어 2040대 기혼 무자녀 그룹으로 비교했습니다."
        return 3, "기혼 무자녀 그룹으로 임시 비교했습니다."

    if youngest_child_stage in {"preschool", "elementary", "young_child"}:
        if age <= 39:
            return 4, ""
        if age == 40 or (40 <= age <= 49):
            return 5, ""
        if age >= 50:
            return 5, "보고서에 50대 초등생 이하 자녀 그룹이 없어 40대 기혼 초등생 이하 자녀 그룹으로 비교했습니다."

    if youngest_child_stage in {"middle_high", "teen"}:
        if 40 <= age <= 49:
            return 6, ""
        if 50 <= age <= 59:
            return 7, ""
        if age < 40:
            return 6, "보고서에 30대 중고등생 자녀 그룹이 없어 40대 기혼 중고등생 자녀 그룹으로 비교했습니다."

    if youngest_child_stage in {"college", "adult_student"}:
        if 50 <= age <= 59:
            return 7, ""
        if 40 <= age <= 49:
            return 6, "대학생 자녀는 40대 기혼 중고등생 자녀 그룹으로 비교했습니다."

    if youngest_child_stage in {"adult", "independent"}:
        if 50 <= age <= 59:
            return 8, ""
        if age < 50:
            return 8, "학업완료 성인 자녀 그룹과 비교했습니다."

    if age >= 50:
        return 8, "가장 유사한 50대 기혼 성인 자녀 그룹으로 비교했습니다."
    return 3, "명확한 그룹이 없어 2040대 기혼 무자녀 그룹으로 비교했습니다."
